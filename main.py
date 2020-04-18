"""

TODO: Ajout du pathfinding
TODO: Ajout du mécanisme berserk
TODO: Ajout de la commande 'suis moi tout près'
TODO: Ajout de la commande 'suis moi à moyenne distance'
TODO: Ajout de la commande 'arrête de me suivre'

"""


import arcade, pathlib

import engine


FOG_OF_WAR_REFRESH_TTL = 10


SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 650
SCREEN_TITLE = "Test"


BROTHER_SCALING = 1
SISTER_SCALING = 1
WALL_SCALING = 1
WEAPON_SCALING = 1
EXCLAMATION_SCALING = 1
GROUND_SCALING = 1


BROTHER_SPEED = 200
SISTER_SPEED = 0.9*BROTHER_SPEED


ASSETS_PATH = pathlib.Path("assets")

BROTHER_SPRITE_PATH = ASSETS_PATH / "brother.png"
SISTER_SPRITE_PATH = ASSETS_PATH / "sister.png"
WALL_SPRITE_PATH = ASSETS_PATH / "wall.png"
WEAPON_SPRITE_PATH = ASSETS_PATH / "weapon.png"
EXCLAMATION_SPRITE_PATH = ASSETS_PATH / "exclamation.png"

DEBUG_MAP_PATH = ASSETS_PATH / "debug_map.tmx"


INVISIBLE = 0
VISIBLE = 255


class Controls:


	UP = arcade.key.Z
	DOWN = arcade.key.S
	LEFT = arcade.key.Q
	RIGHT = arcade.key.D

	SWITCH_CONTROL = arcade.key.A
	TAKE_WEAPON = arcade.key.E


	@staticmethod
	def fill_keyboard(keyboard):

		keyboard[Controls.UP] = False
		keyboard[Controls.DOWN] = False
		keyboard[Controls.LEFT] = False
		keyboard[Controls.RIGHT] = False
		keyboard[Controls.SWITCH_CONTROL] = False
		keyboard[Controls.TAKE_WEAPON] = False


class Game(arcade.Window):

	
	TILE_SIZE = 100


	def __init__(self):

		super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

		self.brothers = None
		self.sisters = None
		self.walls = None
		self.weapons = None
		self.exclamations = None
		self.grounds = None

		self.fog_of_war = None

		self.sight_blocks = []
		self.every_sprites = []

		self.brother = None
		self.sister = None

		self.engine = None

		self.brother_physics_engine = None
		self.sister_physics_engine = None

		self.keyboard = {}
		Controls.fill_keyboard(self.keyboard)

		self.controlled = None

		arcade.set_background_color(arcade.csscolor.BLACK)

		self.mouse_x = 0
		self.mouse_y = 0

		self.fog_of_war_refresh_ttl = 0

	def can_see(self, x, y, dest_x, dest_y):

		line = [[x, y], [dest_x, dest_y]]

		for s in self.sight_blocks:
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

		self.keyboard[symbol] = True

		if symbol == Controls.SWITCH_CONTROL:
			self.controlled.stop_commands()
			self.controlled = [self.engine.brother, self.engine.sister][self.controlled is self.engine.brother]

	def on_key_release(self, symbol: int, modifiers: int):

		self.keyboard[symbol] = False

	def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):

		self.mouse_x = x
		self.mouse_y = y

	def setup(self):

		self.brothers = arcade.SpriteList()
		self.sisters = arcade.SpriteList()
		#self.walls = arcade.SpriteList()
		#self.weapons = arcade.SpriteList()
		self.exclamations = arcade.SpriteList()
		self.fog_of_war = arcade.SpriteList()

		map = arcade.tilemap.read_tmx(str(DEBUG_MAP_PATH))
		self.walls = arcade.tilemap.process_layer(map, "walls", WALL_SCALING)
		self.weapons = arcade.tilemap.process_layer(map, "weapons", WEAPON_SCALING)
		self.grounds = arcade.tilemap.process_layer(map, "ground", GROUND_SCALING)

		self.sight_blocks = self.walls[:]
		self.every_sprites = self.walls[:]
		self.every_sprites += self.weapons
		self.every_sprites += self.grounds

		self.brother = arcade.Sprite(str(BROTHER_SPRITE_PATH), BROTHER_SCALING)
		self.brother.center_x = SCREEN_WIDTH/2
		self.brother.center_y = SCREEN_HEIGHT/2
		self.brothers.append(self.brother)

		self.sister = arcade.Sprite(str(SISTER_SPRITE_PATH), SISTER_SCALING)
		self.sister.center_x = SCREEN_WIDTH/2
		self.sister.center_y = SCREEN_HEIGHT/2
		self.sisters.append(self.sister)

		self.every_sprites += self.brothers
		self.every_sprites += self.sisters

		self.brother_physics_engine = arcade.PhysicsEngineSimple(self.brother, self.walls)
		self.sister_physics_engine = arcade.PhysicsEngineSimple(self.sister, self.walls)

		self.engine = engine.GameEngine.new(
			self.brother.center_x,
			self.brother.center_y,
			self.sister.center_x,
			self.sister.center_y,
		)

		self.controlled = self.engine.brother

		for sprite in self.every_sprites:
			sprite._set_alpha(INVISIBLE)

	def on_draw(self):

		arcade.start_render()

		self.grounds.draw()

		for e in (self.engine.brother, self.engine.sister):

			if e.is_out_leveled and e.associated_exclamation is None:

				s = arcade.Sprite(str(EXCLAMATION_SPRITE_PATH), EXCLAMATION_SCALING)
				s.center_x = e.x
				s.center_y = e.y
				self.exclamations.append(s)
				self.every_sprites.append(s)
				e.associated_exclamation = s

			elif not e.is_out_leveled and e.associated_exclamation is not None:

				e.associated_exclamation.remove_from_sprite_lists()
				e.associated_exclamation = None

		self.walls.draw()
		self.weapons.draw()
		self.brothers.draw()
		self.sisters.draw()
		self.exclamations.draw()

		ui_line_size = 20

		arcade.draw_text(f"Berserk: {self.engine.brother.level:.2f}",
						 self.brother.center_x, self.brother.center_y - ui_line_size,
						 arcade.csscolor.WHITE, 25)

		if self.engine.brother.has_weapon:
			arcade.draw_text("Armé",
							 self.brother.center_x, self.brother.center_y - 2*ui_line_size,
							 arcade.csscolor.WHITE, 25)

		arcade.draw_text(f"Proba: {max(self.engine.brother.level, 0.1):.2f}",
						 self.brother.center_x, self.brother.center_y - 3*ui_line_size,
						 arcade.csscolor.WHITE, 25)

		arcade.draw_text(f"Essai: {self.engine.brother.mood_trial_ttl:.2f}",
						 self.brother.center_x, self.brother.center_y - 4*ui_line_size,
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

	def on_update(self, delta_time: float):

		command_x = 0
		command_y = 0
		if self.keyboard[Controls.LEFT]: command_x -= 1
		if self.keyboard[Controls.RIGHT]: command_x += 1
		if self.keyboard[Controls.UP]: command_y += 1
		if self.keyboard[Controls.DOWN]: command_y -= 1

		self.controlled.set_command(command_x, command_y, BROTHER_SPEED)
		self.controlled.command_take_weapon = self.keyboard[Controls.TAKE_WEAPON]

		self.brother_physics_engine.update()
		self.sister_physics_engine.update()

		self.engine.update(delta_time, self)

		self.fog_of_war_refresh_ttl -= 1

		if self.fog_of_war_refresh_ttl <= 0:

			self.fog_of_war_refresh_ttl = FOG_OF_WAR_REFRESH_TTL

			self.refresh_fog_of_war()

		arcade.set_viewport(
			int(self.controlled.x - SCREEN_WIDTH/2),
			int(self.controlled.x + SCREEN_WIDTH/2),
			int(self.controlled.y - SCREEN_HEIGHT/2),
			int(self.controlled.y + SCREEN_HEIGHT/2),
		)

	def refresh_fog_of_war(self):

		x, y = self.controlled.x, self.controlled.y

		screen_poly = [
			[self.controlled.x - SCREEN_WIDTH//2, self.controlled.y - SCREEN_HEIGHT//2],
			[self.controlled.x - SCREEN_WIDTH//2, self.controlled.y + SCREEN_HEIGHT//2],
			[self.controlled.x + SCREEN_WIDTH//2, self.controlled.y + SCREEN_HEIGHT//2],
			[self.controlled.x + SCREEN_WIDTH//2, self.controlled.y - SCREEN_HEIGHT//2],
		]

		for sprite in self.every_sprites:
			if arcade.are_polygons_intersecting(screen_poly, sprite.points):

				if self.can_see_sprite(x, y, sprite):
					sprite._set_alpha(VISIBLE)

				else:
					sprite._set_alpha(INVISIBLE)


def main():
	window = Game()
	window.setup()
	arcade.run()


if __name__ == "__main__":
	main()
