import tkinter as tk
import random
import math
from PIL import Image, ImageTk


# ============================
#  BASIC GAMEOBJECT
# ============================
class GameObject:
    def __init__(self, canvas, item):
        self.canvas = canvas
        self.item = item

    def delete(self):
        self.canvas.delete(self.item)

    def coords(self):
        return self.canvas.coords(self.item)


# ============================
#  BRICK
# ============================
class Brick(GameObject):
    COLORS = {1: '#4535AA', 2: '#ED639E', 3: '#8FE1A2'}

    def __init__(self, canvas, x, y, hits):
        self.width = 75
        self.height = 20
        self.hits = hits
        color = Brick.COLORS.get(hits, '#CCCCCC')
        item = canvas.create_rectangle(
            x - self.width / 2, y - self.height / 2,
            x + self.width / 2, y + self.height / 2,
            fill=color, tags='brick'
        )
        super().__init__(canvas, item)

    def hit(self):
        self.hits -= 1
        if self.hits <= 0:
            self.delete()
            return True
        else:
            self.canvas.itemconfig(self.item, fill=Brick.COLORS.get(self.hits, '#CCCCCC'))
            return False


# ============================
#  PADDLE
# ============================
class Paddle(GameObject):
    def __init__(self, canvas, x, y, width=110, height=12):
        self.width = width
        self.height = height
        item = canvas.create_rectangle(
            x - width / 2, y - height / 2,
            x + width / 2, y + height / 2,
            fill='#333333', tags='paddle'
        )
        super().__init__(canvas, item)
        self.canvas_width = int(self.canvas['width'])

    def move_to(self, x_center):
        half = self.width / 2
        x1 = max(0, x_center - half)
        x2 = min(self.canvas_width, x_center + half)
        y1, y2 = self.coords()[1], self.coords()[3]
        self.canvas.coords(self.item, x1, y1, x2, y2)


# ============================
#  BALL
# ============================
class Ball(GameObject):
    def __init__(self, canvas, x, y, radius=8, speed=5):
        self.radius = radius
        item = canvas.create_oval(
            x - radius, y - radius,
            x + radius, y + radius,
            fill='#FFAA00', tags='ball'
        )
        super().__init__(canvas, item)
        angle = random.uniform(30, 150)
        rad = math.radians(angle)
        self.vx = speed * math.cos(rad)
        self.vy = -abs(speed * math.sin(rad))
        self.speed = speed

    def move(self):
        self.canvas.move(self.item, self.vx, self.vy)

    def position(self):
        return self.canvas.coords(self.item)

    def bounce_x(self):
        self.vx = -self.vx

    def bounce_y(self):
        self.vy = -self.vy

    def set_speed(self, speed):
        mag = math.hypot(self.vx, self.vy)
        scale = speed / mag
        self.vx *= scale
        self.vy *= scale
        self.speed = speed

    def increase_speed(self, delta):
        self.set_speed(self.speed + delta)


# ============================
#  MAIN GAME
# ============================
class BrickBreaker:
    def __init__(self, width=720, height=520):
        self.root = tk.Tk()
        self.root.title("Brick Breaker")
        self.width = width
        self.height = height
        self.canvas = tk.Canvas(self.root, width=width, height=height)
        self.canvas.pack()

        # ===== BACKGROUND IMAGE =====
        bg_img = Image.open("background.jpg").resize((width, height))
        self.bg = ImageTk.PhotoImage(bg_img)
        self.canvas.create_image(0, 0, image=self.bg, anchor="nw")

        self.score = 0
        self.level = 1
        self.lives = 3
        self.started = False
        self.paused = False

        self.paddle = Paddle(self.canvas, width / 2, height - 30)
        self.ball = Ball(self.canvas, width / 2, height - 60)

        self.score_text = self.canvas.create_text(
            10, 10, anchor='nw',
            text='Score: 0  Lives: 3',
            font=('Helvetica', 16, 'bold'),
            fill='white'
        )
        self.level_text = self.canvas.create_text(
            width - 10, 10, anchor='ne',
            text='Level: 1',
            font=('Helvetica', 16, 'bold'),
            fill='white'
        )

        self.bricks = []
        self.build_level(self.level)

        self.instr = self.canvas.create_text(
            width / 2, height / 2,
            text="Press SPACE to START",
            font=('Helvetica', 26, 'bold'),
            fill='yellow'
        )

        self.canvas.bind('<Motion>', self.mouse_move)
        self.root.bind('<Left>', lambda e: self.keyboard_move(-30))
        self.root.bind('<Right>', lambda e: self.keyboard_move(30))
        self.root.bind('<space>', lambda e: self.start_ball())
        self.root.bind('p', lambda e: self.toggle_pause())
        self.root.bind('r', lambda e: self.restart())

        self.loop()
        self.root.mainloop()

    # ========== LEVEL SYSTEM ==========
    def build_level(self, level):
        for b in self.bricks:
            b.delete()
        self.bricks.clear()

        rows = min(6, 3 + level)
        cols = 8
        mx = 60
        spacing_x = (self.width - 2 * mx) / cols
        top_y = 60

        for r in range(rows):
            for c in range(cols):
                x = mx + spacing_x * c + spacing_x / 2
                y = top_y + r * 26
                hits = min(3, 1 + (r + level) // 2)
                self.bricks.append(Brick(self.canvas, x, y, hits))

    # ========== INPUT ==========
    def mouse_move(self, e):
        self.paddle.move_to(e.x)
        if not self.started and not self.paused:
            px = (self.paddle.coords()[0] + self.paddle.coords()[2]) / 2
            cx = (self.ball.position()[0] + self.ball.position()[2]) / 2
            dx = px - cx
            self.canvas.move(self.ball.item, dx, 0)

    def keyboard_move(self, delta):
        x = (self.paddle.coords()[0] + self.paddle.coords()[2]) / 2 + delta
        self.paddle.move_to(x)

    def start_ball(self):
        if not self.started:
            self.started = True
            self.canvas.delete(self.instr)

    def toggle_pause(self):
        self.paused = not self.paused

    def restart(self):
        self.canvas.delete("all")
        self.__init__()

    # ========== COLLISION ==========
    def check_collision(self):
        bx1, by1, bx2, by2 = self.ball.position()
        if bx1 <= 0 or bx2 >= self.width:
            self.ball.bounce_x()
        if by1 <= 0:
            self.ball.bounce_y()

        px1, py1, px2, py2 = self.paddle.coords()
        if by2 >= py1 and bx2 >= px1 and bx1 <= px2 and self.ball.vy > 0:
            paddle_center = (px1 + px2) / 2
            ball_center = (bx1 + bx2) / 2
            offset = (ball_center - paddle_center) / (self.paddle.width / 2)
            angle = offset * math.radians(75)
            speed = self.ball.speed
            self.ball.vx = speed * math.sin(angle)
            self.ball.vy = -abs(speed * math.cos(angle))

        overlap = self.canvas.find_overlapping(bx1, by1, bx2, by2)
        for item in overlap:
            if 'brick' in self.canvas.gettags(item):
                for b in self.bricks:
                    if b.item == item:
                        destroyed = b.hit()
                        self.score += 10 if destroyed else 5
                        if destroyed:
                            self.bricks.remove(b)
                        self.ball.bounce_y()
                        break

    # ========== GAME LOOP ==========
    def loop(self):
        if not self.paused and self.started:
            self.ball.move()
            self.check_collision()

            bx1, by1, bx2, by2 = self.ball.position()
            if by2 >= self.height:
                self.lives -= 1
                if self.lives <= 0:
                    self.game_over()
                    return
                px = (self.paddle.coords()[0] + self.paddle.coords()[2]) / 2
                self.canvas.coords(self.ball.item, px-8, self.height-60-8, px+8, self.height-60+8)
                self.started = False
                self.instr = self.canvas.create_text(
                    self.width/2, self.height/2,
                    text="Press SPACE to START",
                    font=('Helvetica', 26, 'bold'),
                    fill='yellow'
                )

            if not self.bricks:
                self.level += 1
                self.ball.increase_speed(0.8)
                self.build_level(self.level)
                px = (self.paddle.coords()[0] + self.paddle.coords()[2]) / 2
                self.canvas.coords(self.ball.item, px-8, self.height-60-8, px+8, self.height-60+8)
                self.started = False
                self.instr = self.canvas.create_text(
                    self.width/2, self.height/2,
                    text=f"LEVEL {self.level}\nPress SPACE to START",
                    font=('Helvetica', 26, 'bold'),
                    fill='yellow'
                )

        self.canvas.itemconfig(self.score_text, text=f"Score: {self.score}  Lives: {self.lives}")
        self.canvas.itemconfig(self.level_text, text=f"Level: {self.level}")
        self.root.after(16, self.loop)

    # ========== GAME OVER ==========
    def game_over(self):
        self.canvas.create_text(
            self.width / 2, self.height / 2 - 20,
            text="GAME OVER", font=('Helvetica', 32, 'bold'), fill='red'
        )
        self.canvas.create_text(
            self.width / 2, self.height / 2 + 20,
            text=f"Score: {self.score}\nPress R to restart",
            font=('Helvetica', 18),
            fill='white'
        )
        self.started = False
        self.paused = True


if __name__ == '__main__':
    BrickBreaker()
