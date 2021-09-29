%%writefile agent.py
# for kaggle-environments
from lux.game import Game
from lux.game_map import Cell, RESOURCE_TYPES
from lux.constants import Constants
from lux.game_constants import GAME_CONSTANTS
from lux import annotate
import math
import sys

################################################################################
def find_resources(game_state):
    resource_tiles: list[Cell] = []
    width, height = game_state.map_width, game_state.map_height
    for y in range(height):
        for x in range(width):
            cell = game_state.map.get_cell(x, y)
            if cell.has_resource():
                resource_tiles.append(cell)
    return resource_tiles

################################################################################
def find_empties(game_state):
    empty_tiles: list[Cell] = []
    width, height = game_state.map_width, game_state.map_height
    for y in range(height):
        for x in range(width):
            cell = game_state.map.get_cell(x, y)
            if not cell.has_resource() and cell.citytile == None:
                empty_tiles.append(cell)
    return empty_tiles

################################################################################
def find_closest_empties(pos, empty_tiles, unit_dir):
    closest_st = ''
    closest_dist = math.inf
    closest_empty_tile = None
    for empty_tile in empty_tiles:
        dist = empty_tile.pos.distance_to(pos)
        st = '({}, {})'.format(empty_tile.pos.x, empty_tile.pos.y)
        if st in unit_dir and dist == unit_dir[st]:
            continue
        if dist < closest_dist:
            closest_st = st
            closest_dist = dist
            closest_empty_tile = empty_tile
    return closest_empty_tile, closest_dist, closest_st

################################################################################
def find_closest_resources(pos, player, resource_tiles, unit_dir):
    closest_st = ''
    closest_dist = math.inf
    closest_resource_tile = None
    for resource_tile in resource_tiles:
        if resource_tile.resource.type == Constants.RESOURCE_TYPES.COAL and not player.researched_coal():
            continue
        if resource_tile.resource.type == Constants.RESOURCE_TYPES.URANIUM and not player.researched_uranium():
            continue
        dist = resource_tile.pos.distance_to(pos)
        st = '({}, {})'.format(resource_tile.pos.x, resource_tile.pos.y)
        if st in unit_dir and dist == unit_dir[st]:
            continue
        if dist < closest_dist:
            closest_st = st
            closest_dist = dist
            closest_resource_tile = resource_tile
    return closest_resource_tile, closest_dist, closest_st

################################################################################
def find_closest_city_tile(pos, player):
    closest_city_tile = None
    if len(player.cities) > 0:
        closest_dist = math.inf
        for k, city in player.cities.items():
            for city_tile in city.citytiles:
                dist = city_tile.pos.distance_to(pos)
                if dist < closest_dist:
                    closest_dist = dist
                    closest_city_tile = city_tile
    return closest_city_tile

################################################################################
game_state = None
def agent(observation, configuration):
    global game_state

    ### Do not edit ###
    if observation['step'] == 0:
        game_state = Game()
        game_state._initialize(observation['updates'])
        game_state._update(observation['updates'][2:])
        game_state.id = observation.player
    else:
        game_state._update(observation['updates'])

    actions = []

    ### AI Code goes down here! ###
    player = game_state.players[observation.player]
    opponent = game_state.players[(observation.player + 1) % 2]
    width, height = game_state.map.width, game_state.map.height
    #
    resource_tiles = find_resources(game_state)
    empty_tiles = find_empties(game_state)
    unit_dir = {}
    # 单位动作
    for unit in player.units:
        if unit.is_worker() and unit.can_act():
            if unit.get_cargo_space_left() > 0:                                 # 背包未满
                closest_resource_tile, closest_dist, closest_st = find_closest_resources(unit.pos, player, resource_tiles, unit_dir)
                if closest_resource_tile is not None:
                    action = unit.move(unit.pos.direction_to(closest_resource_tile.pos))
                    actions.append(action)
                    unit_dir[closest_st] = closest_dist
            else:                                                               # 背包满了
                if len(player.units) >= player.city_tile_count:                 # 建城
                    closest_empty_tile, closest_dist, closest_st = find_closest_empties(unit.pos, empty_tiles, unit_dir)
                    if closest_empty_tile is not None:
                        if closest_dist > 0:
                            action = unit.move(unit.pos.direction_to(closest_empty_tile.pos))
                            actions.append(action)
                            unit_dir[closest_st] = closest_dist
                        else:
                            action = unit.build_city()
                            actions.append(action)
                else:                                                           # 回城
                    closest_city_tile = find_closest_city_tile(unit.pos, player)
                    if closest_city_tile is not None:
                        action = unit.move(unit.pos.direction_to(closest_city_tile.pos))
                        actions.append(action)
    # 城市动作
    n_city = player.city_tile_count
    n_unit = len(player.units)
    for k, city in player.cities.items():
        need = city.light_upkeep - city.fuel
        for city_tile in city.citytiles:
            if city_tile.can_act():
                if need > 0 and n_city > n_unit:
                    actions.append(city_tile.build_worker())
                    n_unit += 1
                    need -= 4
                else:
                    actions.append(city_tile.research())
    return actions
