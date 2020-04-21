"""

TODO: Ajout de la commande 'viens ici'
TODO: Ajout du mécanisme berserk
TODO: Ajout de la commande 'suis moi tout près'
TODO: Ajout de la commande 'suis moi à moyenne distance'
TODO: Ajout de la commande 'arrête de me suivre'

"""


import arcade, pathlib, cProfile, pstats

from itertools import chain
from arcade.sprite_list import _SpatialHash

import engine, pathfinder, task

from engine import BROTHER_SPEED, SISTER_SPEED
from animations import EntitySprite
from levels import LevelOne, LevelTwo, LevelThree, LevelFour
from scale import GLOBAL_SCALE


FOG_OF_WAR_REFRESH_TTL = 10
FOG_OF_WAR_ENABLED = False

CLIP = True
CAMERA_ATTACHED = True

#DOOR_INTERACTION_RANGE = 100
DOOR_INTERACTION_RANGE = 30*GLOBAL_SCALE

SOLDIER_RELOAD = 3


SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 650
SCREEN_TITLE = "Test"


ENTITY_SCALING = GLOBAL_SCALE / 1.5
WALL_SCALING = GLOBAL_SCALE
WEAPON_SCALING = GLOBAL_SCALE
EXCLAMATION_SCALING = GLOBAL_SCALE / 10
GROUND_SCALING = GLOBAL_SCALE
GLASS_SCALING = GLOBAL_SCALE
SPAWN_SCALING = GLOBAL_SCALE
PATHFINDER_SCALING = GLOBAL_SCALE
DOORS_SCALING = GLOBAL_SCALE
PROPS_SCALING = GLOBAL_SCALE


ASSETS_PATH = pathlib.Path("assets")
ANIMATIONS_PATH = ASSETS_PATH / "animations"

BROTHER_SPRITE_PATH = ASSETS_PATH / "brother.png"
SISTER_SPRITE_PATH = ASSETS_PATH / "sister.png"
WALL_SPRITE_PATH = ASSETS_PATH / "wall.png"
WEAPON_SPRITE_PATH = ASSETS_PATH / "weapon.png"
EXCLAMATION_SPRITE_PATH = ASSETS_PATH / "exclamation.png"

BROTHER_RUNNING_RIGHT_SCHEME = ANIMATIONS_PATH / "b_running_{}.png"
BROTHER_IDLE_SCHEME = ANIMATIONS_PATH / "b_idle_{}.png"
BROTHER_DEATH_SCHEME = ANIMATIONS_PATH / "b_death_{}.png"
SISTER_RUNNING_RIGHT_SCHEME = ANIMATIONS_PATH / "g_running_{}.png"
SISTER_IDLE_SCHEME = ANIMATIONS_PATH / "g_idle_{}.png"
SISTER_DEATH_SCHEME = ANIMATIONS_PATH / "g_death_{}.png"
SOLDIER_RUNNING_RIGHT_SCHEME = ANIMATIONS_PATH / "s_running_{}.png"
SOLDIER_IDLE_SCHEME = ANIMATIONS_PATH / "s_idle_{}.png"

DYING_GENERIC_SCHEME = ANIMATIONS_PATH / "death_generic_{}.png"

DEBUG_MAP_PATH = ASSETS_PATH / "debug_map.tmx"
HOUSE_MAP_PATH = ASSETS_PATH / "house.tmx"

PLAY_MAP = HOUSE_MAP_PATH

DEBUG_ROUTE = None

LEVELS = {
	2: (ASSETS_PATH / "Jardin.tmx", LevelOne),
	3: (ASSETS_PATH / "Moulin.tmx", LevelTwo),
	4: (ASSETS_PATH / "Cimetierre.tmx", LevelThree),
	5: (ASSETS_PATH / "Eglise.tmx", LevelFour),
}

MAIN_MENU = 0
CREDITS = 1
DEFEAT_BOY = 6
VICTORY = 7
DEFEAT_GIRL = 8
INTRODUCTION = 9

SPACE_TRANSITIONS = {
	CREDITS: MAIN_MENU,
	INTRODUCTION: 2,
	MAIN_MENU: INTRODUCTION,
	VICTORY: MAIN_MENU,
}

NEXT_LEVEL = {
	2: 3,
	3: 4,
	4: 5,
	5: VICTORY,
}


def is_pure_menu(level):
	return level in (MAIN_MENU, CREDITS, DEFEAT_BOY, DEFEAT_GIRL, VICTORY, INTRODUCTION)


INVISIBLE = 0
VISIBLE = 255


def make_static(sprite_list):

	sprite_list.is_static = True

def make_use_spatial_hash(sprite_list):

	sprite_list.use_spatial_hash = True
	sprite_list.spatial_hash = _SpatialHash(cell_size=128)


class Controls:


	UP = arcade.key.Z
	DOWN = arcade.key.S
	LEFT = arcade.key.Q
	RIGHT = arcade.key.D

	SWITCH_CONTROL = arcade.key.A
	TAKE_WEAPON = arcade.key.F
	DOOR = arcade.key.F

	COME_HERE = arcade.key.C

	DEBUG_PRINT_COORD = arcade.key.P
	DEBUG_NO_CLIP = arcade.key.M
	DEBUG_CAMERA_DETACH = arcade.key.O


	@staticmethod
	def fill_keyboard(keyboard):

		keyboard[Controls.UP] = False
		keyboard[Controls.DOWN] = False
		keyboard[Controls.LEFT] = False
		keyboard[Controls.RIGHT] = False
		keyboard[Controls.TAKE_WEAPON] = False


class Bag:


	route_key = None
	route = None


class Camera:


	def __init__(self, x, y, speed=160*GLOBAL_SCALE):

		self.x = x
		self.y = y

		self.dx = 0
		self.dy = 0

		self.speed = speed

	def set_command(self, x, y):

		self.dx = x
		self.dy = y

	def follow(self, obj):

		self.x = obj.x
		self.y = obj.y

	def update(self, dt):

		self.x += self.dx*self.speed*dt
		self.y += self.dy*self.speed*dt


class Game(arcade.Window):


	DEFEAT_BOY = DEFEAT_BOY
	DEFEAT_GIRL = DEFEAT_GIRL

	NEXT_LEVEL = NEXT_LEVEL


	TILE_SIZE = 20*GLOBAL_SCALE

	ORDER_COME_HERE = 0

	ENTITY_KIND_BROTHER = engine.MainEntity.BROTHER
	ENTITY_KIND_SISTER = engine.MainEntity.SISTER
	ENTITY_KIND_SOLDIER = engine.MainEntity.SOLDIER

	DOOR_INTERACTION_RANGE = DOOR_INTERACTION_RANGE


	def __init__(self):

		super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

		self.walls = None
		self.exclamations = None
		self.grounds = None
		self.glasses = None
		self.entities = None
		self.props = None
		self.animators = None
		self.sticks = None
		self.axes = None

		self.doors = None
		self.doors_storage = []
		self.open_doors = None
		self.open_doors_storage = []
		self.door_pairing = [] # [(Sprite (door), Sprite (open))]

		self.spawn = None
		self.pf_data = None

		self.fog_of_war = None

		self.brother = None
		self.sister = None

		self.engine = None

		self.brother_physics_engine = None
		self.brother_glass_physics_engine = None
		self.brother_doors_physics_engine = None
		self.sister_physics_engine = None
		self.sister_glass_physics_engine = None
		self.sister_doors_physics_engine = None

		self.keyboard = {}
		Controls.fill_keyboard(self.keyboard)

		self.controlled = None

		arcade.set_background_color(arcade.csscolor.BLACK)

		self.mouse_x = 0
		self.mouse_y = 0

		self.fog_of_war_refresh_ttl = 0

		#self.current_order = None
		#self.currently_executed_order = None
		#self.current_order_data = None

		self.pf_tree = None
		self.index_pool = None

		self.tasks = {} # {int: Task}

		self.camera = None

		self.level_instance = None

		self.task_keys = None # list

		self.glasses_y_cache = None

		self.current_order_task_key = None

		self.latest_play_level = 2

	def try_shoot(self, soldier, target):

		if self.xcan_see(soldier, target):

			if soldier.reload > 0:
				return

			self.add_task(task.SoldierShot(target.x, target.y))

			soldier.reload = SOLDIER_RELOAD

	def create_route_points(self, x, y, x_dst, y_dst):
		return pathfinder.create_route_points(x, y, x_dst, y_dst, self.index_pool, self)

	def add_task(self, task):

		key = self.index_pool.create()
		self.tasks[key] = task
		self.task_keys.append(key)
		task.setup(self)

		return key

	def rem_task(self, key):

		del self.tasks[key]
		self.index_pool.destroy(key)
		del self.task_keys[self.task_keys.index(key)]

	def xcan_see(self, e1, e2):
		"""

		can e1 see e2 ?

		:param e1:
		:param e2:
		:return:
		"""

		if arcade.is_point_in_polygon(
			x=e2.x,
			y=e2.y,
			polygon_point_list=e1.get_vision_polygon(),
		):
			return self.can_see_sprite(e1.x, e1.y, e2.associated_sprite)

		return False

	def can_see(self, x, y, dest_x, dest_y):

		line = [[x, y], [dest_x, dest_y]]

		for s in chain(self.walls, self.doors):
			if min(x, dest_x) < s.center_x < max(x, dest_x)\
					or min(y, dest_y) < s.center_y < max(y, dest_y):
				if not arcade.is_point_in_polygon(dest_x, dest_y, s.points)\
					and arcade.are_polygons_intersecting(line, s.points):

					return False

		return True

	def can_see_sprite(self, x, y, sprite):

		for point in sprite.points:
			if self.can_see(x, y, *point):
				return True

		return False

	def on_key_press(self, symbol: int, modifiers: int):

		if not self.ready: return

		if is_pure_menu(self.level):

			if symbol == arcade.key.SPACE:

				if self.level in (DEFEAT_GIRL, DEFEAT_BOY):
					self.setup(self.latest_play_level)
					return

				if self.level in SPACE_TRANSITIONS: self.setup(SPACE_TRANSITIONS[self.level])

			if symbol == arcade.key.ENTER:

				if self.level == MAIN_MENU:
					self.setup(CREDITS)

			return

		self.keyboard[symbol] = True

		if symbol == Controls.SWITCH_CONTROL:

			if self.current_order_task_key is not None:

				self.tasks[self.current_order_task_key].quit()
				self.current_order_task_key = None

			if self.controlled.can_be_commanded: self.controlled.stop_commands()
			self.controlled = [self.engine.brother, self.engine.sister][self.controlled is self.engine.brother]

		if symbol == Controls.COME_HERE:

			if self.current_order_task_key is None:

				follower = [self.engine.brother, self.engine.sister][self.controlled is self.engine.brother]
				followed = self.controlled

				if not follower.can_be_commanded:
					print("Cant be commanded")
					return

				self.current_order_task_key = self.add_task(task.XGuideTo(
					follower,
					followed.x,
					followed.y,
				))

		if symbol == Controls.DOOR:

			self.entity_switch_door(self.controlled)

		if symbol == Controls.DEBUG_PRINT_COORD:
			print(f"{int(self.controlled.x)};{int(self.controlled.y)}")

		if symbol == Controls.DEBUG_NO_CLIP:

			global CLIP
			CLIP = not CLIP

			print(f"No clip : {not CLIP}")

		if symbol == Controls.DEBUG_CAMERA_DETACH:

			global CAMERA_ATTACHED
			CAMERA_ATTACHED = not CAMERA_ATTACHED

			print(f"Camera attached : {CAMERA_ATTACHED}")

	def on_key_release(self, symbol: int, modifiers: int):

		if not self.ready: return

		if is_pure_menu(self.level): return

		self.keyboard[symbol] = False

	def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):

		self.mouse_x = x
		self.mouse_y = y

	def entity_switch_door(self, entity):

		player_sprite = entity.associated_sprite

		r = arcade.get_closest_sprite(player_sprite, self.doors)

		if r is None:
			nearest_closed_door, distance_c = None, float("inf")

		else:
			nearest_closed_door, distance_c = r

		r = arcade.get_closest_sprite(player_sprite, self.open_doors)

		if r is None:
			nearest_open_door, distance_o = None, float("inf")

		else:
			nearest_open_door, distance_o = r

		if distance_c < distance_o and distance_c < DOOR_INTERACTION_RANGE:

			for door, open_door in self.door_pairing:

				if door is nearest_closed_door:
					nearest_closed_door.remove_from_sprite_lists()
					self.open_doors.append(open_door)
					break

		if distance_o < distance_c and distance_o < DOOR_INTERACTION_RANGE:

			for door, open_door in self.door_pairing:

				if open_door is nearest_open_door:
					nearest_open_door.remove_from_sprite_lists()
					self.doors.append(door)
					break

	def setup(self, level):

		self.ready = False

		self.level = level

		self.menu = arcade.SpriteList()

		if level == DEFEAT_BOY:

			self.menu.append(arcade.Sprite(
				str(ASSETS_PATH / "Ecrans" / "Ecran de mort garcon.png"),
				center_x=SCREEN_WIDTH//2,
				center_y=SCREEN_HEIGHT//2,
				scale=0.3,
			))

			self.ready = True

		if level == DEFEAT_GIRL:

			self.menu.append(arcade.Sprite(
				str(ASSETS_PATH / "Ecrans" / "Ecran de mort fille.png"),
				center_x=SCREEN_WIDTH//2,
				center_y=SCREEN_HEIGHT//2,
				scale=0.3,
			))

			self.ready = True

		if level == CREDITS:
			self.menu.append(arcade.Sprite(
				str(ASSETS_PATH / "Ecrans" / "Crédits.png"),
				center_x=SCREEN_WIDTH // 2,
				center_y=SCREEN_HEIGHT // 2,
				scale=0.3,
			))

			self.ready = True

		if level == INTRODUCTION:
			self.menu.append(arcade.Sprite(
				str(ASSETS_PATH / "Ecrans" / "Introduction.png"),
				center_x=SCREEN_WIDTH // 2,
				center_y=SCREEN_HEIGHT // 2,
				scale=0.3,
			))

			self.ready = True

		if level == MAIN_MENU:

			self.menu.append(arcade.Sprite(
				str(ASSETS_PATH / "Ecrans" / "Ecran titre.png"),
				center_x=SCREEN_WIDTH // 2,
				center_y=SCREEN_HEIGHT // 2,
				scale=0.3,
			))

			self.ready = True

		if is_pure_menu(self.level): return

		print("Setting up ...")

		self.latest_play_level = level

		data = LEVELS[level]

		#self.walls = arcade.SpriteList()
		#self.weapons = arcade.SpriteList()
		self.exclamations = arcade.SpriteList()
		self.fog_of_war = arcade.SpriteList()
		self.entities = arcade.SpriteList()
		self.animators = arcade.SpriteList()

		map = arcade.tilemap.read_tmx(str(data[0]))
		self.map = map
		self.walls = arcade.tilemap.process_layer(map, "walls", WALL_SCALING)
		print("Walls")
		self.sticks = arcade.tilemap.process_layer(map, "sticks", WEAPON_SCALING)
		print("Sticks")
		self.axes = arcade.tilemap.process_layer(map, "axes", WEAPON_SCALING)
		print("Axes")
		self.grounds = arcade.tilemap.process_layer(map, "ground", GROUND_SCALING)
		print("Grounds")
		self.glasses = arcade.tilemap.process_layer(map, "glasses", GLASS_SCALING)
		print("Glasses")
		self.spawn = arcade.tilemap.process_layer(map, "spawn", SPAWN_SCALING)
		print("Spawn")
		self.pf_data = arcade.tilemap.process_layer(map, "pathfinder", PATHFINDER_SCALING)
		print("PF data")
		self.doors = arcade.tilemap.process_layer(map, "doors", DOORS_SCALING)
		print("Doors")
		self.open_doors = arcade.tilemap.process_layer(map, "open_doors", DOORS_SCALING)
		print("Open doors")
		self.props = arcade.tilemap.process_layer(map, "props", PROPS_SCALING)
		print("Props")

		#make_static(self.walls)
		#make_static(self.grounds); make_use_spatial_hash(self.grounds)
		#make_static(self.pf_data); make_use_spatial_hash(self.pf_data)

		self.doors_storage = self.doors[:]
		self.open_doors_storage = self.open_doors[:]

		while self.open_doors:
			self.open_doors[0].remove_from_sprite_lists()

		self.door_pairing = []

		for door in self.open_doors_storage:

			closed_door, distance = arcade.get_closest_sprite(door, self.doors)
			self.door_pairing.append((closed_door, door))
			print(str(distance))

		if self.spawn:
			spawn_x = self.spawn[0].center_x
			spawn_y = self.spawn[0].center_y

		else:
			spawn_x = 0
			spawn_y = 0

		self.glasses_y_cache = []

		for sprite in self.glasses:
			self.glasses_y_cache.append((sprite._get_bottom(), sprite, 0))

		self.glasses_y_cache = sorted(self.glasses_y_cache, key=lambda i: i[0], reverse=True)

		#self.brother = arcade.Sprite(str(BROTHER_SPRITE_PATH), ENTITY_SCALING)

		demonics = ASSETS_PATH / "Démonique"
		demon_pace = 2

		self.brother = EntitySprite(
			running_right_file_scheme=str(BROTHER_RUNNING_RIGHT_SCHEME),
			running_right_amount=5,
			running_right_pace=0.5,
			idle_right_file_scheme=str(BROTHER_IDLE_SCHEME),
			idle_right_amount=2,
			idle_pace=2,
			dying_right_file_scheme=str(BROTHER_DEATH_SCHEME),
			dying_right_amount=2,
			dying_right_pace=4,
			m_scale=ENTITY_SCALING,
			scale=ENTITY_SCALING,
			kind="brother",
			running_right_s_demon_scheme=str(demonics / "Semi démon {}.png"),
			running_right_s_demon_amount=5,
			running_right_s_demon_pace=demon_pace,
			running_right_demon_scheme=str(demonics / "Démon {}.png"),
			running_right_demon_amount=5,
			running_right_demon_pace=demon_pace,
			running_right_demon_stick_scheme=str(demonics / "Démon avec bâton {}.png"),
			running_right_demon_stick_amount=5,
			running_right_demon_stick_pace=demon_pace,
			running_right_demon_axe_scheme=str(demonics / "Démon avec hache {}.png"),
			running_right_demon_axe_amount=5,
			running_right_demon_axe_pace=demon_pace,
		)

		self.brother.center_x = spawn_x
		self.brother.center_y = spawn_y
		self.entities.append(self.brother)

		#self.sister = arcade.Sprite(str(SISTER_SPRITE_PATH), ENTITY_SCALING)

		self.sister = EntitySprite(
			running_right_file_scheme=str(SISTER_RUNNING_RIGHT_SCHEME),
			running_right_amount=5,
			running_right_pace=0.5,
			idle_right_file_scheme=str(SISTER_IDLE_SCHEME),
			idle_right_amount=2,
			idle_pace=2,
			dying_right_file_scheme=str(SISTER_DEATH_SCHEME),
			dying_right_amount=2,
			dying_right_pace=4,
			m_scale=ENTITY_SCALING,
			scale=ENTITY_SCALING,
		)

		self.sister.center_x = spawn_x
		self.sister.center_y = spawn_y
		self.entities.append(self.sister)

		self.brother_physics_engine = arcade.PhysicsEngineSimple(self.brother, self.walls)
		self.brother_glass_physics_engine = arcade.PhysicsEngineSimple(self.brother, self.glasses)
		self.brother_doors_physics_engine = arcade.PhysicsEngineSimple(self.brother, self.doors)
		self.sister_physics_engine = arcade.PhysicsEngineSimple(self.sister, self.walls)
		self.sister_glass_physics_engine = arcade.PhysicsEngineSimple(self.sister, self.glasses)
		self.sister_doors_physics_engine = arcade.PhysicsEngineSimple(self.sister, self.doors)

		self.engine = engine.GameEngine.new(
			self,
			self.brother.center_x,
			self.brother.center_y,
			self.sister.center_x,
			self.sister.center_y,
		)

		self.engine.brother.associated_sprite = self.brother
		self.engine.sister.associated_sprite = self.sister

		self.controlled = self.engine.brother

		self.camera = Camera(0, 0)
		self.camera.follow(self.controlled)

		print("Camera set up")

		if FOG_OF_WAR_ENABLED:
			for sprite in chain(self.grounds, self.entities, self.walls, self.glasses, self.doors, self.open_doors, self.sticks, self.axes):
				sprite._set_alpha(INVISIBLE)

		self.pf_tree = pathfinder.Tree.generate(self)
		self.index_pool = pathfinder.IndexPool.new()

		self.task_keys = []

		self.level_instance = data[1]()
		self.level_instance.setup(self)

		"""
		self.add_task(task.After(2,
								 lambda self=self:
								 self.debug_shot()
								 ))
		"""

		self.ready = True

	def debug_shot(self):

		self.add_task(task.SoldierShot(self.brother.center_x, self.brother.center_y))
		self.add_task(task.After(2,
								 lambda self=self:
								 self.debug_shot()
								 ))

	def draw_out_level_indicators(self):

		for e in (self.engine.brother, self.engine.sister):

			if e.is_out_leveled and e.associated_exclamation is None:

				s = arcade.Sprite(str(EXCLAMATION_SPRITE_PATH), EXCLAMATION_SCALING)
				s.center_x = e.x
				s.center_y = e.y
				self.exclamations.append(s)
				e.associated_exclamation = s

			elif not e.is_out_leveled and e.associated_exclamation is not None:

				e.associated_exclamation.remove_from_sprite_lists()
				e.associated_exclamation = None

	def draw_debug(self):

		ui_line_size = 20

		arcade.draw_text(f"Berserk: {self.engine.brother.level:.2f}",
						 self.brother.center_x, self.brother.center_y - ui_line_size,
						 arcade.csscolor.WHITE, 25)

		if self.engine.brother.has_weapon:
			arcade.draw_text("Armé",
							 self.brother.center_x, self.brother.center_y - 2 * ui_line_size,
							 arcade.csscolor.WHITE, 25)

		arcade.draw_text(f"Proba: {max(self.engine.brother.level, 0.1):.2f}",
						 self.brother.center_x, self.brother.center_y - 3 * ui_line_size,
						 arcade.csscolor.WHITE, 25)

		arcade.draw_text(f"Essai: {self.engine.brother.mood_trial_ttl:.2f}",
						 self.brother.center_x, self.brother.center_y - 4 * ui_line_size,
						 arcade.csscolor.WHITE, 25)

		arcade.draw_text(f"Panique: {self.engine.sister.level:.2f}",
						 self.sister.center_x, self.sister.center_y - ui_line_size,
						 arcade.csscolor.WHITE, 25)

		"""
		for r in (engine.BROTHER_BERSERK_DECREASE_RANGE, engine.BROTHER_BERSERK_INCREASE_RANGE):
			arcade.draw_circle_outline(
				self.brother.center_x,
				self.brother.center_y,
				r,
				arcade.csscolor.WHITE,
			)
		"""

		for e in (self.engine.sister, self.engine.brother):
			arcade.draw_text(f"{e.x:.2f};{e.y:.2f}",
							 e.x, e.y + 2 * ui_line_size,
							 arcade.csscolor.WHITE, 25)

		for r in (engine.SISTER_PANIC_DECREASE_RANGE, engine.SISTER_PANIC_INCREASE_RANGE):
			arcade.draw_circle_outline(
				self.sister.center_x,
				self.sister.center_y,
				r,
				arcade.csscolor.WHITE,
			)

		ig_mouse = (
			self.controlled.x - (SCREEN_WIDTH / 2) + self.mouse_x,
			self.controlled.y - (SCREEN_HEIGHT / 2) + self.mouse_y,
		)

		color = [arcade.csscolor.RED, arcade.csscolor.WHITE][self.can_see(
			self.controlled.x, self.controlled.y,
			*ig_mouse,
		)]

		arcade.draw_line(self.controlled.x, self.controlled.y,
						 *ig_mouse,
						 color)

		global DEBUG_ROUTE
		if DEBUG_ROUTE is not None: arcade.draw_lines(DEBUG_ROUTE, arcade.csscolor.GREEN)

	def on_draw(self):

		if not self.ready: return

		arcade.start_render()

		self.menu.draw()

		if is_pure_menu(self.level):
			return

		if CAMERA_ATTACHED:
			self.camera.follow(self.controlled)

		self.grounds.draw()

		#self.draw_out_level_indicators()

		self.walls.draw()
		self.doors.draw()
		self.open_doors.draw()

		sprs = sorted(chain(
			self.glasses_y_cache,
			[(sprite._get_bottom(), sprite, 1) for sprite in self.entities]
		), key=lambda i: i[0], reverse=True)

		"""
		self.glasses.draw()

		for entity in self.entities:
			entity.texture.draw_scaled(
				center_x=entity.center_x,
				center_y=entity.center_y,
				scale=ENTITY_SCALING,
			)
		"""

		for y, sprite, t in sprs:

			if t == 0:
				sprite.draw()

			else:
				sprite.texture.draw_scaled(
					center_x=sprite.center_x,
					center_y=sprite.center_y,
					scale=ENTITY_SCALING
				)

		self.engine.sister.try_health_display()

		self.exclamations.draw()
		self.sticks.draw()
		self.axes.draw()

		for animator in self.animators:
			animator.texture.draw_scaled(
				center_x=animator.center_x,
				center_y=animator.center_y,
				scale=animator.m_scale,
			)

		#for e in self.engine.entities.values():
		#	e.draw_vision()

		#self.draw_debug()
		#self.draw_pf()

	def draw_pf(self):

		if self.current_order_task_key is None:
			return

		t = self.tasks[self.current_order_task_key]
		key = t.key

		for node in self.pf_tree.nodes:

			h = node.safe.get(key, {"height": None})["height"]

			arcade.draw_text(
				text=str(h) + f" {node.rx};{node.ry}",
				start_x=node.x - 20,
				start_y=node.y,
				color=arcade.csscolor.WHITE,
				font_size=10,
			)

			for sub_node in node.links.values():
				arcade.draw_line(
					node.x,
					node.y,
					sub_node.x,
					sub_node.y,
					color=arcade.csscolor.WHITE,
				)

	"""
	def update_order(self):

		if self.current_order != self.currently_executed_order:

			self.currently_executed_order = self.current_order

			if self.current_order == Game.ORDER_COME_HERE:

				followed = self.controlled
				follower = [self.engine.brother, self.engine.sister][self.controlled is self.engine.brother]

				self.current_order_data = Bag()

				points, key = pathfinder.create_route_points(
					src_x=follower.x,
					src_y=follower.y,
					dst_x=followed.x,
					dst_y=followed.y,
					index_pool=self.index_pool,
					game=self,
				)

				if points is None:
					print("Unable to do that")
					self.current_order = None
					return

				global DEBUG_ROUTE
				DEBUG_ROUTE = points

				self.current_order_data.route_key = key
				self.current_order_data.route = points

		if self.current_order == Game.ORDER_COME_HERE:

			follower = [self.engine.brother, self.engine.sister][self.controlled is self.engine.brother]

			if abs(follower.x - self.current_order_data.route[0][0]) < 10\
				and abs(follower.y - self.current_order_data.route[0][1]) < 10:
				del self.current_order_data.route[0]

			if self.current_order_data.route:
				follower.set_command(
					self.current_order_data.route[0][0] - follower.x,
					self.current_order_data.route[0][1] - follower.y,
				)

			else:
				follower.stop_commands()
				self.current_order = None
				
	"""

	def update_checking_keyboard(self):

		command_x = 0
		command_y = 0
		if self.keyboard[Controls.LEFT]: command_x -= 1
		if self.keyboard[Controls.RIGHT]: command_x += 1
		if self.keyboard[Controls.UP]: command_y += 1
		if self.keyboard[Controls.DOWN]: command_y -= 1

		if CAMERA_ATTACHED:

			if self.controlled.can_be_commanded:
				self.controlled.set_command(command_x, command_y)

		else:
			self.camera.set_command(command_x, command_y)

		self.controlled.command_take_weapon = self.keyboard[Controls.TAKE_WEAPON]

	def update_fog_of_war(self):

		self.fog_of_war_refresh_ttl -= 1

		if self.fog_of_war_refresh_ttl <= 0:

			self.fog_of_war_refresh_ttl = FOG_OF_WAR_REFRESH_TTL

			self.refresh_fog_of_war()

	def update_tasks(self, dt):

		to_be_rem = []

		for key in self.task_keys:

			self.tasks[key].update(dt, self)

			if not self.tasks[key].is_alive(self):
				to_be_rem.append(key)

		for key in to_be_rem:
			self.rem_task(key)

	def deal_with_out_level_and_order(self):

		if not self.engine.brother.can_be_commanded\
			or not self.engine.sister.can_be_commanded:

			if self.current_order_task_key is not None:

				self.tasks[self.current_order_task_key].quit()
				self.current_order_task_key = None

	def on_update(self, delta_time: float):

		if not self.ready: return

		if is_pure_menu(self.level):
			return

		self.camera.update(delta_time)

		self.deal_with_out_level_and_order()

		#self.update_order()

		self.update_checking_keyboard()

		self.update_tasks(delta_time)

		if CLIP:

			self.brother_physics_engine.update()
			self.brother_glass_physics_engine.update()
			self.brother_doors_physics_engine.update()
			self.sister_physics_engine.update()
			self.sister_glass_physics_engine.update()
			self.sister_doors_physics_engine.update()

		else:
			self.brother.center_x += self.brother.change_x
			self.brother.center_y += self.brother.change_y
			self.sister.center_x += self.sister.change_x
			self.sister.center_y += self.sister.change_y

		self.engine.update(delta_time, self)

		if FOG_OF_WAR_ENABLED: self.update_fog_of_war()

		arcade.set_viewport(
			int(self.camera.x - SCREEN_WIDTH/2),
			int(self.camera.x + SCREEN_WIDTH/2),
			int(self.camera.y - SCREEN_HEIGHT/2),
			int(self.camera.y + SCREEN_HEIGHT/2),
		)

		for entity in self.entities:
			entity.update_animation(delta_time)

		#self.brother.update_animation(delta_time, self.engine.brother.demon_state, self.engine.brother.weapon_t)

		self.brother.demon_state = self.engine.brother.demon_state
		self.brother.weapon = self.engine.brother.weapon_t

		if self.current_order_task_key not in self.tasks:
			self.current_order_task_key = None

		self.level_instance.update(delta_time)

	def refresh_fog_of_war(self):

		x, y = self.controlled.x, self.controlled.y

		screen_poly = [
			[self.controlled.x - SCREEN_WIDTH//2, self.controlled.y - SCREEN_HEIGHT//2],
			[self.controlled.x - SCREEN_WIDTH//2, self.controlled.y + SCREEN_HEIGHT//2],
			[self.controlled.x + SCREEN_WIDTH//2, self.controlled.y + SCREEN_HEIGHT//2],
			[self.controlled.x + SCREEN_WIDTH//2, self.controlled.y - SCREEN_HEIGHT//2],
		]

		for sprite in chain(self.grounds, self.entities, self.walls, self.glasses, self.doors, self.open_doors, self.axes, self.sticks):
			if arcade.is_point_in_polygon(sprite.center_x, sprite.center_y, screen_poly):

				if self.can_see_sprite(x, y, sprite):
					sprite._set_alpha(VISIBLE)

				else:
					sprite._set_alpha(INVISIBLE)

	def player_sprite(self):
		return [self.brother, self.sister][self.controlled is self.engine.sister]

	def new_entity(self, x, y, kind):
		return engine.MainEntity.new(x=x, y=y, kind=kind, game=self)

	def new_solider_animated_sprite(self):
		return EntitySprite(
			running_right_file_scheme=str(SOLDIER_RUNNING_RIGHT_SCHEME),
			running_right_amount=5,
			running_right_pace=0.5,
			idle_right_file_scheme=str(SOLDIER_IDLE_SCHEME),
			idle_right_amount=2,
			idle_pace=2,
			dying_right_file_scheme=str(DYING_GENERIC_SCHEME),
			dying_right_amount=3,
			dying_right_pace=4,
			m_scale=ENTITY_SCALING,
		)

	def add_entity(self, entity, sprite):

		key = self.index_pool.create()
		self.engine.entities[key] = entity
		entity.associated_sprite = sprite
		entity.associated_physics_engine = arcade.PhysicsEngineSimple(sprite, arcade.SpriteList())
		sprite.center_x = entity.x
		sprite.center_y = entity.y
		self.entities.append(sprite)
		return key

	def rem_entity(self, key):

		self.engine.entities[key].associated_sprite.remove_from_sprite_lists()
		del self.engine.entities[key]
		self.index_pool.destroy(key)


def main():
	window = Game()
	window.setup(MAIN_MENU)
	arcade.run()


if __name__ == "__main__":

	profile = cProfile.Profile()
	profile.runcall(main)

	ps = pstats.Stats(profile)
	ps.dump_stats("perf_logs.txt")
	#ps.print_stats()
