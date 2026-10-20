import sys, pygame
import random
import os
import math
import numpy as np
import matplotlib.pyplot as plt
import ast

os.environ['SDL_AUDIODRIVER'] = 'dsp'
pygame.init()
saved_diseases = open("saved.txt", "a")
saved_diseases.close()

# Base Variables
SIZE = (600, 400)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
GRAY = (128, 128, 128)
PINK = (255, 192, 203)
SPEED = 1

# Main window
screen = pygame.display.set_mode(SIZE)
pygame.display.set_caption("Disease Propagation")
CLOCK = pygame.time.Clock()

# Defines function to find distance between 2 points
def distance(point1, point2):
    return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)

# Defines function which uses recursion and a logrithmic algorithm to find all the circles that are colliding
def collisions(points, colliding_points):
    n = len(points)

    # Base case: If there are three or fewer points, calculate the perimeter of the triangle directly
    if n == 2:
        if distance(points[0], points[1]) <= 16:
            colliding_points.append((points[0], points[1]))
            return colliding_points
    elif n < 2:
        return colliding_points

    # Sort points by x-coordinate and y-coordinate
    points.sort(key=lambda p: (p[0], p[1]))

    # Divide points into two equal parts by x-coordinate
    left_half = points[:n // 2]
    right_half = points[n // 2:]

    median_line_x = (left_half[-1][0] + right_half[0][0]) / 2
    points_within_distance = [point for point in points if abs(point[0] - median_line_x) <= 8]

    for i in range(len(points_within_distance) - 1):
        if distance(points_within_distance[i], points_within_distance[i + 1]) <= 16:
            colliding_points.append((points_within_distance[i], points_within_distance[i + 1]))

    collisions(left_half, colliding_points)
    collisions(right_half, colliding_points)

    return colliding_points

# Defines main class used for the people in the simulation
class Person():
    # Class vairables
    radius = 8
    speed = SPEED

    # Initializes person
    def __init__(self, cont, distancing, recovery_death_speed, mortality, recovered_immunity, initial_infected, center):
        self.center = center
        self.cont = cont
        self.distancing = True if random.randint(1, 100) <= distancing else False
        self.recovery_death_speed = recovery_death_speed
        self.mortality = mortality
        self.recovered_immunity = True if recovered_immunity == 1 else False

        self.state = "sick" if random.randint(1, 100) <= initial_infected else "healthy"
        self.start_day = 0

        self.colour = GREEN
        self.direction = random.randint(1, 360) * (math.pi / 180)
        self.xc = math.cos(self.direction)
        self.yc = math.sin(self.direction)

    # Updates person every frame
    def update(self, day, people, dead_people):
        if self.state == "sick":
            self.colour = RED
            if day - self.start_day >= self.recovery_death_speed:
                if random.randint(1, 100) <= self.mortality:
                    people.remove(self)
                    dead_people.append(self)
                else:
                    if self.recovered_immunity:
                        self.state = "recovered"
                        self.colour = PINK
                    else:
                        self.state = "healthy"
                        self.colour = GREEN

        if self.distancing is False:
            self.center = (self.center[0] + self.speed * self.xc, self.center[1] + self.speed * self.yc)

        if self.center[0] >= 577:
            self.center = (576, self.center[1])
            self.xc = -self.xc
        elif self.center[0] <= 23:
            self.center = (24, self.center[1])
            self.xc = -self.xc

        if self.center[1] >= 376:
            self.center = (self.center[0], 375)
            self.yc = -self.yc
        elif self.center[1] <= 83:
            self.center = (self.center[0], 84)
            self.yc = -self.yc

        pygame.draw.circle(screen, self.colour, self.center, self.radius)

    # What to do when colliding with someone else
    def collided(self, p2, day):

        if self.state == "healthy" and p2.state == "sick":
            if random.randint(1, 100) <= self.cont:
                self.start_day = day
                self.state = "sick"

        self.xc = -self.xc
        self.yc = -self.yc
        while distance(self.center, p2.center) < 17:
            self.center = (self.center[0] + self.speed * self.xc, self.center[1] + self.speed * self.yc)
            pygame.draw.circle(screen, self.colour, self.center, self.radius)

# Shows plot of disease data at the end
def show_plot(x_vals, y_vals, z_vals, max_day, title='Title', x_label='X-axis', y_label='Y-axis',
              colors=['green', 'red', 'magenta']):
    # Create an array with the positions of each bar along the x-axis
    barWidth = 0.25
    r1 = np.arange(max_day)
    r2 = [x + barWidth for x in r1]
    r3 = [x + barWidth for x in r2]

    # Create the bars
    plt.bar(r1, x_vals, color=colors[0], width=barWidth, edgecolor='grey', label='Healthy')
    plt.bar(r2, y_vals, color=colors[1], width=barWidth, edgecolor='grey', label='Sick')
    plt.bar(r3, z_vals, color=colors[2], width=barWidth, edgecolor='grey', label='Recovered')

    # Add xticks on the middle of the group bars
    plt.xlabel(x_label, fontweight='bold')
    plt.ylabel(y_label, fontweight='bold')
    plt.xticks([r + barWidth for r in range(max_day)], range(1, max_day + 1))

    # Create legend & Show graphic
    plt.title(title)
    plt.legend()

    # use .show instead of the above two lines to display the plot
    plt.show()

# Main simulation
def simulation(cont, population, distancing, recovery_speed, mortality, recovered_immunity, initial_infected):
    people = []
    dead_people = []
    # Makes sure values are usable
    if population > 3 or population < 1:
        population = 2
    if cont > 100 or cont < 0:
        cont = 50
    if distancing > 100 or distancing < 0:
        distancing = 50
    if recovery_speed < 0:
        recovery_speed = 3
    if mortality > 100 or mortality < 0:
        mortality = 50
    if initial_infected > 100 or initial_infected < 0:
        initial_infected = 50

    # Creates population
    for x in range(50, 560, population * 75):
        for y in range(95, 370, 50):
            people.append(
                Person(cont, distancing, recovery_speed, mortality, recovered_immunity, initial_infected, (x, y)))

    sim_speed = 2000
    day = 0
    start_time = pygame.time.get_ticks()

    # Healthy, recovered, dead people every day
    plot_vals_h = []
    plot_vals_r = []
    plot_vals_s = []

    # Controls:
    for i in range(10):
        print()
    print("Press left and right arrow keys to change the speed, and the space_bar to end the simulation.")

    while True:
        screen.fill(WHITE)
        centers = []
        centersP = {}
        colliding_points = []
        TICK = 90000 // sim_speed

        # Speed and Day text
        speed_font = pygame.font.Font('freesansbold.ttf', 22)
        speed_text = speed_font.render(f'Speed: {TICK}', True, BLACK)
        day_text = speed_font.render(f'Day: {day}', True, BLACK)
        screen.blit(speed_text, (450, 20))
        screen.blit(day_text, (20, 20))

        # Add Days
        if pygame.time.get_ticks() - start_time >= sim_speed:
            healthy = 0
            recovered = 0
            sick = 0
            for person in people:
                state = person.state
                if state == "healthy":
                    healthy += 1
                elif state == "recovered":
                    recovered += 1
                elif state == "sick":
                    sick += 1

            plot_vals_h.append(healthy)
            plot_vals_r.append(recovered)
            plot_vals_s.append(sick)

            day += 1
            start_time = pygame.time.get_ticks()

            if day >= 365:
                weeks = (day // 7) + 1
                x_vals = [plot_vals_h[i] for i in range(0, len(plot_vals_h), 7)]
                y_vals = [plot_vals_s[i] for i in range(0, len(plot_vals_s), 7)]
                z_vals = [plot_vals_r[i] for i in range(0, len(plot_vals_r), 7)]
                show_plot(x_vals, y_vals, z_vals, weeks, 'Disease Stats', 'Week', 'Amount of People',
                          ['green', 'red', 'magenta'])
                break

        # Title
        title_font = pygame.font.Font('freesansbold.ttf', 32)
        title_text = title_font.render('Simulation', True, BLACK)
        screen.blit(title_text, (200, 15))

        # Boundaries
        top = pygame.Rect((0, 60), (600, 15))
        bottom = pygame.Rect((0, 385), (600, 15))
        left = pygame.Rect((0, 75), (15, 310))
        right = pygame.Rect((585, 75), (15, 310))
        pygame.draw.rect(screen, GRAY, top)
        pygame.draw.rect(screen, GRAY, bottom)
        pygame.draw.rect(screen, GRAY, left)
        pygame.draw.rect(screen, GRAY, right)

        # Updates each person and their collisions
        for person in people:
            person.update(day, people, dead_people)
            centers.append(person.center)
            centersP[person.center] = person

        cols = collisions(centers, colliding_points)
        for points in cols:
            p1 = centersP[points[0]]
            p2 = centersP[points[1]]
            p1.collided(p2, day)
            p2.collided(p1, day)

        # Event handler
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT and sim_speed >= 333:
                    sim_speed -= 30
                if event.key == pygame.K_LEFT and sim_speed <= 9750:
                    sim_speed += 50
                if event.key == pygame.K_SPACE:
                    weeks = (day // 7) + 1
                    x_vals = [plot_vals_h[i] for i in range(0, len(plot_vals_h), 7)]
                    y_vals = [plot_vals_s[i] for i in range(0, len(plot_vals_s), 7)]
                    z_vals = [plot_vals_r[i] for i in range(0, len(plot_vals_r), 7)]
                    show_plot(x_vals, y_vals, z_vals, weeks, 'Disease Stats', 'Week', 'Amount of People',
                              ['green', 'red', 'magenta'])
                    break

        CLOCK.tick(TICK)
        pygame.display.flip()

# New screen which asks for factors of the new disease
def new():
    factors = []
    prompt = 0
    while True:
        screen.fill(WHITE)

        # Event handler
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                break

        #Inputs
        prompts = ["Enter percentage chance of getting infected after contact (contagiousness): ",
                   "Enter the population size 1-3 (1 being largest, 3 being smallest): ",
                   "Enter the percentage of the population social distancing: ",
                   "Enter the amount of days it will take to recover: ",
                   "Enter the mortality rate (percentage): ",
                   "Enter 1 if recovered immunity is true, and 2 if it is false: ",
                   "Enter the percentage of the population that will start infected: "]
        curr_prompt = prompts[prompt]
        prompt_font = pygame.font.Font('freesansbold.ttf', 16)
        prompt_text = prompt_font.render(f'{curr_prompt}', True, BLACK)
        screen.blit(prompt_text, (5, 200))

        pygame.display.flip()

        curr_factor = int(input(curr_prompt))
        factors.append(curr_factor)
        prompt += 1
        if len(factors) == 7:
            print()
            save_it = int(input("Would you like to save this disease? (1 for yes, 2 for no): "))
            if save_it == 1:
                name = input("Enter the name of the disease: ")
                saved_diseases = open("saved.txt", "a")
                saved_diseases.write(name + " " + str(factors))
                saved_diseases.write("\n")
                saved_diseases.close()

            simulation(factors[0], factors[1], factors[2], factors[3], factors[4], factors[5], factors[6])

        CLOCK.tick(30)

# Saved menu to cycle through saved diseases
def saved():
    print("Click left and right arrow keys to cycle through saved diseases.")
    print("Press enter to start the simulation for the selected disease.")
    saved = open("saved.txt", "r")
    length = -1
    lines = []
    for line in saved:
        lines.append(line)
        length += 1
    curr_line = 0

    # Current saved attributes
    curr_saved = lines[curr_line]

    name = ""
    for letter in curr_saved:
        if letter != "[":
            name = name + letter
        else:
            break
    factor_list_str = ""
    for i in range(len(curr_saved) - 1, -1, -1):
        if curr_saved[i] != "[":
            factor_list_str = factor_list_str + curr_saved[i]
        else:
            factor_list_str = factor_list_str + "["
            break

    factor_list_str = factor_list_str[::-1]
    factor_list = ast.literal_eval(factor_list_str)
    rec_imm = True if factor_list[5] == 1 else False

    while True:
        screen.fill(WHITE)

        title_font = pygame.font.Font('freesansbold.ttf', 32)
        title_text = title_font.render(f"Saved: {name}", True, BLACK)
        screen.blit(title_text, (5, 20))

        factor_font = pygame.font.Font('freesansbold.ttf', 22)

        cont_text = factor_font.render(f"Contagiousness: {factor_list[0]}", True, BLACK)
        pop_text = factor_font.render(f"Population Size: {factor_list[1]}", True, BLACK)
        dist_text = factor_font.render(f"Social Distancing: {factor_list[2]}", True, BLACK)
        rec_time_text = factor_font.render(f"Recovery Days: {factor_list[3]}", True, BLACK)
        mort_rate_text = factor_font.render(f"Mortality Rate: {factor_list[4]}", True, BLACK)
        rec_imm_text = factor_font.render(f"Recovered Immunity: {rec_imm}", True, BLACK)
        init_infec_text = factor_font.render(f"Initial Infected: {factor_list[6]}", True, BLACK)

        screen.blit(cont_text, (15, 60))
        screen.blit(pop_text, (15, 100))
        screen.blit(dist_text, (15, 140))
        screen.blit(rec_time_text, (15, 180))
        screen.blit(mort_rate_text, (15, 220))
        screen.blit(rec_imm_text, (15, 260))
        screen.blit(init_infec_text, (15, 300))

        # Event handler
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                break
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT and curr_line < length:
                    curr_line += 1
                    # Updates saved attributes
                    curr_saved = lines[curr_line]

                    name = ""
                    for letter in curr_saved:
                        if letter != "[":
                            name = name + letter
                        else:
                            break
                    factor_list_str = ""
                    for i in range(len(curr_saved) - 1, -1, -1):
                        if curr_saved[i] != "[":
                            factor_list_str = factor_list_str + curr_saved[i]
                        else:
                            factor_list_str = factor_list_str + "["
                            break

                    factor_list_str = factor_list_str[::-1]
                    factor_list = ast.literal_eval(factor_list_str)
                    rec_imm = True if factor_list[5] == 1 else False

                elif event.key == pygame.K_LEFT and curr_line > 0:
                    curr_line -= 1
                    # Updates saved attributes
                    curr_saved = lines[curr_line]

                    name = ""
                    for letter in curr_saved:
                        if letter != "[":
                            name = name + letter
                        else:
                            break
                    factor_list_str = ""
                    for i in range(len(curr_saved) - 1, -1, -1):
                        if curr_saved[i] != "[":
                            factor_list_str = factor_list_str + curr_saved[i]
                        else:
                            factor_list_str = factor_list_str + "["
                            break

                    factor_list_str = factor_list_str[::-1]
                    factor_list = ast.literal_eval(factor_list_str)
                    rec_imm = True if factor_list[5] == 1 else False
                elif event.key == pygame.K_RETURN:
                    simulation(factor_list[0], factor_list[1], factor_list[2], factor_list[3], factor_list[4],
                               factor_list[5], factor_list[6])
        pygame.display.flip()

# Main menu
def menu():
    # Menu Text
    title_font = pygame.font.Font('freesansbold.ttf', 32)
    selection_font = pygame.font.Font('freesansbold.ttf', 32)
    title_text = title_font.render('Disease Propagation', True, BLACK)
    selection_text_new = selection_font.render('New', True, BLACK)
    selection_text_saved = selection_font.render('Saved', True, BLACK)
    selection_text_new_rect = selection_text_new.get_rect()
    selection_text_saved_rect = selection_text_saved.get_rect()
    selection_text_new_rect.center = (150, 200)
    selection_text_saved_rect.center = (410, 200)
    selection_new_bg = pygame.Rect((0, 0), (100, 50))
    selection_saved_bg = pygame.Rect((0, 0), (120, 50))
    selection_new_bg.center = selection_text_new_rect.center
    selection_saved_bg.center = selection_text_saved_rect.center
    new_bg_c = GREEN
    saved_bg_c = RED
    while True:
        screen.fill(WHITE)
        mouse_pos = pygame.mouse.get_pos()

        # Event handler
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                break

            if event.type == pygame.MOUSEBUTTONDOWN:
                if selection_new_bg.collidepoint(mouse_pos):
                    new()
                elif selection_saved_bg.collidepoint(mouse_pos):
                    saved()

        # Selection text
        screen.blit(title_text, (145, 15))
        pygame.draw.rect(screen, new_bg_c, selection_new_bg)
        pygame.draw.rect(screen, saved_bg_c, selection_saved_bg)
        screen.blit(selection_text_new, selection_text_new_rect)
        screen.blit(selection_text_saved, selection_text_saved_rect)

        # Selection collision
        if selection_new_bg.collidepoint(mouse_pos):
            new_bg_c = GRAY
        elif selection_saved_bg.collidepoint(mouse_pos):
            saved_bg_c = GRAY
        else:
            new_bg_c = GREEN
            saved_bg_c = RED

        CLOCK.tick(30)
        pygame.display.flip()


menu()