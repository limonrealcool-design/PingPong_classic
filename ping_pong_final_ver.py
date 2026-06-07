import pygame
import sys
import random
import math

# Инициализация Pygame и его модулей
pygame.init()
pygame.mixer.init()

# ------------------------------------------------------------
# Константы окна
# ------------------------------------------------------------
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
WIN_SCORE = 5  # Очки, необходимые для победы
TIME_LIMIT = 120  # Лимит времени в секундах (2 минуты)

# ------------------------------------------------------------
# Цвета (R, G, B)
# ------------------------------------------------------------
# Фоновые цвета для градиента
COLOR_TOP = (25, 25, 80)  # Тёмно-синий верх
COLOR_BOTTOM = (60, 60, 120)  # Более светлый синий низ

WHITE = (255, 255, 255)
LIGHT_GRAY = (180, 180, 200)
GRAY = (120, 120, 140)
YELLOW = (255, 240, 0)
BLUE_PADDLE = (0, 150, 255)
RED_PADDLE = (255, 60, 60)

# ------------------------------------------------------------
# Загрузка звуков
# ------------------------------------------------------------
try:
    hit_sound = pygame.mixer.Sound("the-sound-of-hitting-the-ball.mp3")  # Звук при отбивании мяча
except:
    hit_sound = None

try:
    score_sound = pygame.mixer.Sound("victory.mp3")  # Звук при пропущенном голе
except:
    score_sound = None


def play_sound(sound):
    """Воспроизводит звук, если он был успешно загружен."""
    if sound:
        sound.play()


def create_gradient_surface(width, height, color_top, color_bottom):
    """Создаёт поверхность с вертикальным линейным градиентом."""
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    for y in range(height):
        t = y / height
        r = int(color_top[0] * (1 - t) + color_bottom[0] * t)
        g = int(color_top[1] * (1 - t) + color_bottom[1] * t)
        b = int(color_top[2] * (1 - t) + color_bottom[2] * t)
        pygame.draw.line(surface, (r, g, b), (0, y), (width, y))
    return surface


def draw_circle_alpha(screen, color, center, radius):
    """Рисует круг с поддержкой альфа-канала."""
    target_rect = pygame.Rect(center[0] - radius, center[1] - radius, radius * 2, radius * 2)
    shape_surf = pygame.Surface(target_rect.size, pygame.SRCALPHA)
    pygame.draw.circle(shape_surf, color, (radius, radius), radius)
    screen.blit(shape_surf, target_rect)


# ------------------------------------------------------------
# Класс частицы для анимации ударов и голов
# ------------------------------------------------------------
class Particle:
    def __init__(self, x, y, dx, dy, lifetime, color, size=3):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.lifetime = lifetime  # Оставшееся время жизни в кадрах
        self.max_lifetime = lifetime  # Исходное время жизни
        self.color = color
        self.size = size

    def update(self):
        """Обновить положение и уменьшить время жизни."""
        self.x += self.dx
        self.y += self.dy
        self.lifetime -= 1

    def draw(self, screen):
        """Нарисовать частицу с плавным исчезновением."""
        if self.lifetime > 0:
            alpha = int(255 * (self.lifetime / self.max_lifetime))
            color_with_alpha = (*self.color[:3], alpha)
            draw_circle_alpha(screen, color_with_alpha, (int(self.x), int(self.y)), self.size)


def spawn_particles(particles, x, y, count, color, spread=2.0, speed_range=(2, 5)):
    """Создать набор частиц в заданной точке."""
    for _ in range(count):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(*speed_range)
        dx = math.cos(angle) * speed
        dy = math.sin(angle) * speed
        lifetime = random.randint(15, 30)
        particles.append(Particle(x, y, dx, dy, lifetime, color))


# ------------------------------------------------------------
# Класс платформы (ракетки)
# ------------------------------------------------------------
class Paddle:
    def __init__(self, x, y, width, height, color):
        self.rect = pygame.Rect(x, y, width, height)
        self.speed = 7
        self.width = width
        self.height = height
        self.color = color

    def move_up(self):
        self.rect.y -= self.speed
        if self.rect.top < 0:
            self.rect.top = 0

    def move_down(self):
        self.rect.y += self.speed
        if self.rect.bottom > SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect, border_radius=self.width // 2)


# ------------------------------------------------------------
# Класс мяча
# ------------------------------------------------------------
class Ball:
    def __init__(self, x, y, size, speed):
        self.rect = pygame.Rect(x - size // 2, y - size // 2, size, size)
        self.size = size
        self.speed = speed
        self.dx = 0
        self.dy = 0
        self.color = YELLOW
        self.trail = []  # След из последних позиций
        self.max_trail = 15
        self.reset(random.choice([-1, 1]))

    def reset(self, direction_x):
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        angle = random.uniform(-math.pi / 4, math.pi / 4)
        self.dx = self.speed * math.cos(angle) * direction_x
        self.dy = self.speed * math.sin(angle)
        self.trail.clear()

    def update(self, particles):
        # Обновление следа
        self.trail.append((self.rect.centerx, self.rect.centery, self.max_trail))
        for i in range(len(self.trail)):
            x, y, age = self.trail[i]
            self.trail[i] = (x, y, age - 1)
        self.trail = [t for t in self.trail if t[2] > 0]

        self.rect.x += self.dx
        self.rect.y += self.dy

        if self.rect.top <= 0:
            self.rect.top = 0
            self.dy = abs(self.dy)
            spawn_particles(particles, self.rect.centerx, self.rect.top, 8, YELLOW)
            play_sound(hit_sound)
        elif self.rect.bottom >= SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT
            self.dy = -abs(self.dy)
            spawn_particles(particles, self.rect.centerx, self.rect.bottom, 8, YELLOW)
            play_sound(hit_sound)

    def draw(self, screen):
        # Рисуем след
        for i, (x, y, age) in enumerate(self.trail):
            alpha = int(100 * (age / self.max_trail))
            size = int(self.size * (0.5 + 0.5 * age / self.max_trail))
            color = (255, 240, 0, alpha)
            draw_circle_alpha(screen, color, (int(x), int(y)), size // 2)
        # Сам мяч
        pygame.draw.ellipse(screen, self.color, self.rect)

    def hit_paddle(self, paddle, particles):
        if self.rect.colliderect(paddle.rect):
            hit_x = self.rect.centerx
            hit_y = self.rect.centery
            if self.dx > 0:
                base_angle = math.pi
            else:
                base_angle = 0
            for _ in range(12):
                angle = base_angle + random.uniform(-math.pi / 3, math.pi / 3)
                speed = random.uniform(1.5, 4)
                dx = math.cos(angle) * speed
                dy = math.sin(angle) * speed
                lifetime = random.randint(12, 25)
                particles.append(Particle(hit_x, hit_y, dx, dy, lifetime, WHITE))

            offset = (self.rect.centery - paddle.rect.centery) / (paddle.height / 2)
            angle = offset * (math.pi / 3)
            self.dx = -self.dx
            current_speed = math.hypot(self.dx, self.dy)
            self.dy = current_speed * math.sin(angle)
            self.dx = math.copysign(math.sqrt(current_speed ** 2 - self.dy ** 2), self.dx)
            self.dx *= 1.02
            self.dy *= 1.02
            play_sound(hit_sound)
            if self.dx > 0:
                self.rect.left = paddle.rect.right + 1
            else:
                self.rect.right = paddle.rect.left - 1


# ------------------------------------------------------------
# Функции экранов меню, управления и завершения
# ------------------------------------------------------------
def draw_text(screen, text, size, color, center):
    """Вывести текст заданного размера и цвета по центру."""
    font = pygame.font.Font(None, size)
    surface = font.render(text, True, color)
    rect = surface.get_rect(center=center)
    screen.blit(surface, rect)


def draw_gradient_background(screen):
    """Заливает экран градиентным фоном."""
    gradient = create_gradient_surface(SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_TOP, COLOR_BOTTOM)
    screen.blit(gradient, (0, 0))


def show_controls(screen):
    """Показывает экран с описанием управления."""
    while True:
        draw_gradient_background(screen)
        draw_text(screen, "УПРАВЛЕНИЕ", 60, WHITE, (SCREEN_WIDTH // 2, 60))

        # Заголовки режимов
        draw_text(screen, "Одиночный режим:", 40, YELLOW, (SCREEN_WIDTH // 2, 140))
        draw_text(screen, "Стрелки ВВЕРХ и ВНИЗ - движение платформы", 30, WHITE, (SCREEN_WIDTH // 2, 190))

        draw_text(screen, "Многопользовательский режим:", 40, YELLOW, (SCREEN_WIDTH // 2, 250))
        draw_text(screen, "Левый игрок: клавиши W (вверх) и S (вниз)", 30, WHITE, (SCREEN_WIDTH // 2, 300))
        draw_text(screen, "Правый игрок: стрелки ВВЕРХ и ВНИЗ", 30, WHITE, (SCREEN_WIDTH // 2, 340))

        draw_text(screen, "Во время игры:", 40, YELLOW, (SCREEN_WIDTH // 2, 410))
        draw_text(screen, "ESC - выход в главное меню", 30, WHITE, (SCREEN_WIDTH // 2, 460))

        draw_text(screen, "Нажмите любую клавишу для возврата в меню", 25, GRAY, (SCREEN_WIDTH // 2, 550))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                return  # Возвращаемся в предыдущее меню


def choose_mode(screen):
    """Экран выбора режима."""
    while True:
        draw_gradient_background(screen)
        draw_text(screen, "ПИНГ-ПОНГ", 80, WHITE, (SCREEN_WIDTH // 2, 150))
        draw_text(screen, "Выберите режим:", 40, LIGHT_GRAY, (SCREEN_WIDTH // 2, 270))
        draw_text(screen, "1 - Одиночная игра", 35, WHITE, (SCREEN_WIDTH // 2, 330))
        draw_text(screen, "2 - Два игрока", 35, WHITE, (SCREEN_WIDTH // 2, 380))
        draw_text(screen, "3 - Управление", 35, WHITE, (SCREEN_WIDTH // 2, 430))
        draw_text(screen, "ESC - выход", 25, GRAY, (SCREEN_WIDTH // 2, 500))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    return "single"
                if event.key == pygame.K_2:
                    return "multi"
                if event.key == pygame.K_3:
                    return "controls"
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()


def choose_level(screen):
    """Экран выбора уровня сложности."""
    while True:
        draw_gradient_background(screen)
        draw_text(screen, "УРОВЕНЬ СЛОЖНОСТИ", 50, WHITE, (SCREEN_WIDTH // 2, 180))
        draw_text(screen, "1 - Лёгкий", 35, WHITE, (SCREEN_WIDTH // 2, 270))
        draw_text(screen, "2 - Средний", 35, WHITE, (SCREEN_WIDTH // 2, 330))
        draw_text(screen, "3 - Сложный", 35, WHITE, (SCREEN_WIDTH // 2, 390))
        draw_text(screen, "ESC - назад", 25, GRAY, (SCREEN_WIDTH // 2, 500))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    return "easy"
                if event.key == pygame.K_2:
                    return "medium"
                if event.key == pygame.K_3:
                    return "hard"
                if event.key == pygame.K_ESCAPE:
                    return "back_to_mode"


def game_over_screen(screen, score1, score2, elapsed_time):
    """Финальный экран с результатами."""
    while True:
        draw_gradient_background(screen)
        draw_text(screen, "ИГРА ОКОНЧЕНА", 60, WHITE, (SCREEN_WIDTH // 2, 140))
        draw_text(screen, f"Игрок 1: {score1}    Игрок 2: {score2}", 45, WHITE, (SCREEN_WIDTH // 2, 240))
        if score1 > score2:
            winner = "Победил Игрок 1!"
        elif score2 > score1:
            winner = "Победил Игрок 2!"
        else:
            winner = "Ничья!"
        draw_text(screen, winner, 50, YELLOW, (SCREEN_WIDTH // 2, 320))
        draw_text(screen, f"Время: {int(elapsed_time)} с", 35, LIGHT_GRAY, (SCREEN_WIDTH // 2, 390))
        draw_text(screen, "Q - выход   R - рестарт   ESC - меню", 28, WHITE, (SCREEN_WIDTH // 2, 500))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    return "quit"
                if event.key == pygame.K_r:
                    return "restart"
                if event.key == pygame.K_ESCAPE:
                    return "menu"


# ------------------------------------------------------------
# Главная игровая функция
# ------------------------------------------------------------
def game_loop(screen, mode, level):
    """Основной цикл игры с анимациями."""
    clock = pygame.time.Clock()

    level_settings = {
        "easy": {"paddle_h": 120, "ball_speed": 4, "ai_speed": 4},
        "medium": {"paddle_h": 90, "ball_speed": 6, "ai_speed": 6},
        "hard": {"paddle_h": 60, "ball_speed": 8, "ai_speed": 8},
    }
    settings = level_settings[level]
    paddle_h = settings["paddle_h"]
    paddle_w = 15

    left_paddle = Paddle(30, SCREEN_HEIGHT // 2 - paddle_h // 2, paddle_w, paddle_h, BLUE_PADDLE)
    right_paddle = Paddle(SCREEN_WIDTH - 30 - paddle_w, SCREEN_HEIGHT // 2 - paddle_h // 2, paddle_w, paddle_h,
                          RED_PADDLE)

    ai_controlled = (mode == "single")
    ball = Ball(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, 20, settings["ball_speed"])
    particles = []

    score_left = 0
    score_right = 0
    score_anim_left_scale = 1.0
    score_anim_right_scale = 1.0

    start_ticks = pygame.time.get_ticks()
    time_elapsed = 0
    running = True
    game_active = True

    field_bg = create_gradient_surface(SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_TOP, COLOR_BOTTOM)

    while running:
        clock.tick(FPS)
        time_elapsed = (pygame.time.get_ticks() - start_ticks) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "menu"

        if game_active:
            keys = pygame.key.get_pressed()
            if mode == "multi":
                if keys[pygame.K_w]:
                    left_paddle.move_up()
                if keys[pygame.K_s]:
                    left_paddle.move_down()
                if keys[pygame.K_UP]:
                    right_paddle.move_up()
                if keys[pygame.K_DOWN]:
                    right_paddle.move_down()
            else:
                if keys[pygame.K_UP]:
                    left_paddle.move_up()
                if keys[pygame.K_DOWN]:
                    left_paddle.move_down()
                if ai_controlled:
                    if ball.rect.centery < right_paddle.rect.centery:
                        right_paddle.rect.y -= settings["ai_speed"]
                    elif ball.rect.centery > right_paddle.rect.centery:
                        right_paddle.rect.y += settings["ai_speed"]
                    if right_paddle.rect.top < 0:
                        right_paddle.rect.top = 0
                    if right_paddle.rect.bottom > SCREEN_HEIGHT:
                        right_paddle.rect.bottom = SCREEN_HEIGHT

        if game_active:
            ball.update(particles)

            if ball.rect.left <= 0:
                score_right += 1
                score_anim_right_scale = 2.0
                spawn_particles(particles, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, 25, RED_PADDLE, speed_range=(3, 6))
                play_sound(score_sound)
                ball.reset(direction_x=1)
            elif ball.rect.right >= SCREEN_WIDTH:
                score_left += 1
                score_anim_left_scale = 2.0
                spawn_particles(particles, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, 25, BLUE_PADDLE, speed_range=(3, 6))
                play_sound(score_sound)
                ball.reset(direction_x=-1)

            ball.hit_paddle(left_paddle, particles)
            ball.hit_paddle(right_paddle, particles)

            if score_left >= WIN_SCORE or score_right >= WIN_SCORE or time_elapsed >= TIME_LIMIT:
                game_active = False

        # Анимация счёта
        if score_anim_left_scale > 1.0:
            score_anim_left_scale = max(1.0, score_anim_left_scale - 0.06)
        if score_anim_right_scale > 1.0:
            score_anim_right_scale = max(1.0, score_anim_right_scale - 0.06)

        for p in particles[:]:
            p.update()
            if p.lifetime <= 0:
                particles.remove(p)

        # Отрисовка
        screen.blit(field_bg, (0, 0))

        for y in range(15, SCREEN_HEIGHT, 30):
            pygame.draw.circle(screen, GRAY, (SCREEN_WIDTH // 2, y), 3)

        left_paddle.draw(screen)
        right_paddle.draw(screen)
        ball.draw(screen)

        for p in particles:
            p.draw(screen)

        # Счёт с анимацией
        font = pygame.font.Font(None, 50)
        left_text = font.render(str(score_left), True, WHITE)
        if score_anim_left_scale > 1.0:
            w, h = left_text.get_size()
            left_text = pygame.transform.smoothscale(left_text,
                                                     (int(w * score_anim_left_scale), int(h * score_anim_left_scale)))
        left_rect = left_text.get_rect()
        right_text = font.render(str(score_right), True, WHITE)
        if score_anim_right_scale > 1.0:
            w, h = right_text.get_size()
            right_text = pygame.transform.smoothscale(right_text, (
            int(w * score_anim_right_scale), int(h * score_anim_right_scale)))
        right_rect = right_text.get_rect()
        screen.blit(left_text, (SCREEN_WIDTH // 2 - 30 - left_rect.width, 20))
        screen.blit(right_text, (SCREEN_WIDTH // 2 + 30, 20))

        timer_font = pygame.font.Font(None, 40)
        timer_surface = timer_font.render(f"Время: {int(time_elapsed)}", True, LIGHT_GRAY)
        screen.blit(timer_surface, (SCREEN_WIDTH // 2 - timer_surface.get_width() // 2, 70))

        hint_font = pygame.font.Font(None, 22)
        hint = hint_font.render("ESC - меню", True, GRAY)
        screen.blit(hint, (10, SCREEN_HEIGHT - 25))

        pygame.display.flip()

        if not game_active:
            result = game_over_screen(screen, score_left, score_right, time_elapsed)
            return result


# ------------------------------------------------------------
# Главная функция
# ------------------------------------------------------------
def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Пинг-Понг")

    # Попытка загрузить и включить фоновую музыку
    try:
        pygame.mixer.music.load("relaxed_scene.mp3")  # или .ogg
        pygame.mixer.music.set_volume(0.3)  # тихая громкость (30%)
        pygame.mixer.music.play(-1)  # бесконечное повторение
        print("Фоновая музыка запущена.")
    except pygame.error:
        print("Файл relaxed_scene.mp3 не найден. Игра будет без музыки.")

    while True:
        mode_choice = choose_mode(screen)
        if mode_choice == "controls":
            show_controls(screen)
            continue
        mode = mode_choice
        while True:
            level = choose_level(screen)
            if level == "back_to_mode":
                break
            result = game_loop(screen, mode, level)
            if result == "quit":
                pygame.mixer.music.stop()  # остановить музыку при выходе
                pygame.quit()
                sys.exit()
            elif result == "menu":
                break

    pygame.mixer.music.stop()
    pygame.quit()
    sys.exit()

print("Игра может быть без звуков, Извините!")

if __name__ == "__main__":
    main()

