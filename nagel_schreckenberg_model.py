import numpy as np
import os
from time import sleep
import argparse
import pandas as pd

class Car():
    def __init__(self, position, emoji):
        self.speed = 0
        self.position = position
        self.emoji = emoji

class TrafficLight():
    def __init__(self, position, time):
        self.position = position
        self.time = time
        self.state = False
        self.set_state_emoji()

    def set_state_emoji(self):
        if self.state:
            self.emoji = "\U0001F534"
        else:
            self.emoji = "\U0001F7E2"

    def toggle_state(self):
        self.state = not self.state
        self.set_state_emoji()

class Road():
    def __init__(self, road_size, num_cars, max_speed, brake_prob, num_episodes, flux_marker_position = None, traffic_lights_positions = None, traffic_lights_times = 20):
        self.road = [{"c":None, "t":None} for _ in range(road_size)] 
        self.road_size = road_size
        self.num_cars = num_cars
        self.max_speed = max_speed
        self.brake_prob = brake_prob
        self.num_episodes = num_episodes
        self.traffic_lights_positions = traffic_lights_positions
        self.traffic_lights_times = traffic_lights_times
        self.car_emojis = ["\U0001F68C", "\U0001F68E", "\U0001F690", "\U0001F691", "\U0001F692", "\U0001F693", "\U0001F695", "\U0001F697", "\U0001F699", "\U0001F69A", "\U0001F69B", "\U0001F6FA", "\U0001F6FB", "\U0001F6F5", "\U0001F6B4", "\U0001F3CD", "\U0001F9BC", "\U0001F3CE", "\U0001F3C7", "\U0001F9BD"]
        self.set_flux_marker_position(flux_marker_position)
        self.flux_counter = 0
        self.flux_sum = 0
        self.flux = 0.0
        self.flux_across_time = []
        self.add_traffic_lights()
        self.populate_road()

    def set_flux_marker_position(self, position):
        if position:
            self.flux_marker = position
        else:
            self.flux_marker = int((self.road_size-1) / 2)

    def add_traffic_lights(self):
        if self.traffic_lights_positions != None:
            if isinstance(self.traffic_lights_positions, list):
                for tlp, tlt in zip(self.traffic_lights_positions, self.traffic_lights_times):
                    self.road[tlp]["t"] = TrafficLight(tlp, tlt)
            else:
                self.road[self.traffic_lights_positions]["t"] = TrafficLight(self.traffic_lights_positions, self.traffic_lights_times)
            
    def populate_road(self):
        cars_positions = np.random.choice(self.road_size, self.num_cars, replace=False)
        cars_positions.sort()
        for p in cars_positions:
            self.road[p]["c"] = Car(p, np.random.choice(self.car_emojis))

    def print_road(self):
        sleep(0.10)
        os.system("clear")

        for section in self.road:
            if section["t"]:
                print(f"{section['t'].emoji}", end="")
            else:
                print(" ", end="")
        print("")

        for section in self.road:
            if section["c"]:
                print(f"{section['c'].emoji}", end="")
            else:
                print("=", end="")  
        print("")

    def verify_closed_traffic_lights(self, begin_range, end_range):
        if self.traffic_lights_positions != None:
            if isinstance(self.traffic_lights_positions, list):
                traffic_lights_in_range = [t for t in self.traffic_lights_positions if t in range(begin_range, end_range)]
                for i in traffic_lights_in_range:
                    if self.road[i]["t"].state:
                        return True
            else:
                if self.traffic_lights_positions in range(begin_range, end_range):
                    if self.road[self.traffic_lights_positions]["t"].state:
                        return True
    
    def verify_collision_or_closed_traffic_lights(self, car):
        speed = car.speed
        position = car.position
        distance = 0

        while(speed > 0):
            position = (position - 1 + self.road_size) % self.road_size
            speed-=1
            distance += 1
            if self.road[position]["c"] or self.verify_closed_traffic_lights(position, (position - 1 + self.road_size) % self.road_size):
                return distance, position, True
        
        return distance, position, False
    
    def update_traffic_lights(self, current_time):
        if self.traffic_lights_positions != None:
            if isinstance(self.traffic_lights_positions, list):
                for p in self.traffic_lights_positions:
                    if current_time > 0:
                        if current_time % self.road[p]["t"].time == 0:
                            self.road[p]["t"].toggle_state()
            else:
                if current_time > 0:
                    if current_time % self.road[self.traffic_lights_positions]["t"].time == 0:
                        self.road[self.traffic_lights_positions]["t"].toggle_state()
            
    def update_speed_cars(self):
        for section in self.road:
            if section["c"]:
                if section["c"].speed < self.max_speed and all(not x["c"] for x in self.road[max(0, section["c"].position - section["c"].speed - 1):section["c"].position]) and all(not x["c"] for x in self.road[min(self.road_size + (section["c"].position - section["c"].speed - 1), self.road_size):self.road_size]) and (not self.verify_closed_traffic_lights(max(0, section["c"].position - section["c"].speed - 1), section["c"].position)) and (not self.verify_closed_traffic_lights(min(self.road_size + (section["c"].position - section["c"].speed - 1), self.road_size), self.road_size)):
                    section["c"].speed+=1
                elif  section["c"].speed > 0:
                    distance, position, must_reduce = self.verify_collision_or_closed_traffic_lights(section["c"])
                    if must_reduce:
                        section["c"].speed = distance-1
                if section["c"].speed > 0 and np.random.choice(a=[False, True], p=[1-self.brake_prob, self.brake_prob]):
                    section["c"].speed -= 1


    def flux_counter_verifier(self, init_position, end_position):
        found_flux_counter = False
        while(init_position != end_position):
            if init_position == self.flux_marker:
                found_flux_counter = True
                break
            init_position = (init_position - 1 + self.road_size) % self.road_size
            
        return found_flux_counter and (self.flux_marker != end_position)

    def move_cars(self):
        new_road = [None] * self.road_size
        for section in self.road:
            if section["c"]:
                new_position = (section["c"].position - section["c"].speed + self.road_size) % self.road_size
                if self.road[new_position]["c"] and section["c"].speed > 0: #Really necessary?
                   new_position = (new_position + 1) % self.road_size
                   section["c"].speed -= 1
                if self.flux_counter_verifier(section["c"].position, new_position):
                    self.flux_counter += 1
                section["c"].position = new_position
                new_road[section["c"].position] = section["c"]

        self.flux_sum += self.flux_counter   
        self.flux_across_time.append(self.flux_counter)
        self.flux_counter = 0

        for i, car in enumerate(new_road):
            if car:
                self.road[i]["c"] = car
            else:
                self.road[i]["c"] = None

    def calculate_average_flux(self):
        return self.flux_sum / self.num_episodes
    
    def run(self, terminal_printing = True):
        self.flux_across_time = []
        if terminal_printing:
            self.print_road()
        for i in range(self.num_episodes):
            self.update_traffic_lights(i)
            self.update_speed_cars()
            self.move_cars()
            if terminal_printing:
                self.print_road()
        self.calculate_average_flux()
        return self.flux_across_time



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-rs", "--road_size", type=int, help="Specify how many positions the array representing the road must have.")
    parser.add_argument("-nc", "--num_cars", type=int, help="Specify how many cars the simulation must have.")
    parser.add_argument("-ms", "--max_speed", type=int, help="Specify the maximum number of positions per time step a car can travel.")
    parser.add_argument("-bp", "--brake_prob", type=float, help="Specify the probability a car have to randomly braking.")
    parser.add_argument("-ne", "--num_episodes", type=int, help="Specify how many iterations will the simulation have.")
    parser.add_argument("-tp", "--traffic_lights_positions", nargs='*', type=int, help="Specify in which indexes of the array road are the traffic lights going to be.")
    parser.add_argument("-tt", "--traffic_lights_times", nargs='*', type=int, help="Specify how many time steps are the traffic lights going to remain closed/open.")
    args = parser.parse_args()
    r = Road(args.road_size, args.num_cars, args.max_speed, args.brake_prob, args.num_episodes, args.traffic_lights_positions, args.traffic_lights_times)
    r.run()
