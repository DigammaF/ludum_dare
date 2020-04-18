"""

TODO: Ajout du pathfinding
TODO: Ajout du mécanisme berserk
TODO: Ajout de la commande 'suis moi tout près'
TODO: Ajout de la commande 'suis moi à moyenne distance'
TODO: Ajout de la commande 'arrête de me suivre'

"""


import arcade, pathlib

import engine


SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 650
SCREEN_TITLE = "Test"


TILE_SIZE = 100


BROTHER_SCALING = 1
SISTER_SCALING = 1
WALL_SCALING = 1
WEAPON_SCALING = 1
EXCLAMATION_SCALING = 1


BROTHER_SPEED = 200
SISTER_SPEED = 0.9*BROTHER_SPEED


ASSETS_PATH = pathlib.Path("assets")

BROTHER_SPRITE_PATH = ASSETS_PATH / "brother.png"
SISTER_SPRITE_PATH = ASSETS_PATH / "sister.png"
WALL_SPRITE_PATH = ASSETS_PATH / "wall.png"
WEAPON_SPRITE_PATH = ASSETS_PATH / "weapon.png"
EXCLAMATION_SPRITE_PATH = ASSETS_PATH / "exclamation.png"

DEBUG_MAP_PATH = ASSETS_PATH / "debug_map.tmx"


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

	def __init__(self):

		super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

		self.brothers = None
		self.sisters = None
		self.walls = None
		self.weapons = None
		self.exclamations = None

		self.brother = None
		self.sister = None

		self.engine = None

		self.brother_physics_engine = None
		self.sister_physics_engine = None

		self.keyboard = {}
		Controls.fill_keyboard(self.keyboard)

		self.controlled = None

		arcade.set_background_color(arcade.csscolor.CORNFLOWER_BLUE)

	def on_key_press(self, symbol: int, modifiers: int):

		self.keyboard[symbol] = True

		if symbol == Controls.SWITCH_CONTROL:
			self.controlled.stop_commands()
			self.controlled = [self.engine.brother, self.engine.sister][self.controlled is self.engine.brother]

	def on_key_release(self, symbol: int, modifiers: int):

		self.keyboard[symbol] = False

	def setup(self):

		self.brothers = arcade.SpriteList()
		self.sisters = arcade.SpriteList()
		#self.walls = arcade.SpriteList()
		#self.weapons = arcade.SpriteList()
		self.exclamations = arcade.SpriteList()

		map = arcade.tilemap.read_tmx(str(DEBUG_MAP_PATH))
		self.walls = arcade.tilemap.process_layer(map, "walls", WALL_SCALING)
		self.weapons = arcade.tilemap.process_layer(map, "weapons", WEAPON_SCALING)

		self.brother = arcade.Sprite(str(BROTHER_SPRITE_PATH), BROTHER_SCALING)
		self.brother.center_x = SCREEN_WIDTH/2
		self.brother.center_y = SCREEN_HEIGHT/2
		self.brothers.append(self.brother)

		self.sister = arcade.Sprite(str(SISTER_SPRITE_PATH), SISTER_SCALING)
		self.sister.center_x = SCREEN_WIDTH/2
		self.sister.center_y = SCREEN_HEIGHT/2
		self.sisters.append(self.sister)

		self.brother_physics_engine = arcade.PhysicsEngineSimple(self.brother, self.walls)
		self.sister_physics_engine = arcade.PhysicsEngineSimple(self.sister, self.walls)

		self.engine = engine.GameEngine.new(
			self.brother.center_x,
			self.brother.center_y,
			self.sister.center_x,
			self.sister.center_y,
		)

		self.controlled = self.engine.brother

	def on_draw(self):

		arcade.start_render()

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

	def on_update(self, delta_time: float):

		command_x = 0
		command_y = 0
		if self.keyboard[Controls.LEFT]: command_x -= 1
		if self.keyboard[Controls.RIGHT]: command_x += 1
		if self.keyboard[Controls.UP]: command_y += 1
		if self.keyboard[Controls.DOWN]: command_y -= 1

		self.controlled.set_command(command_x, command_y, BROTHER_SPEED)

		self.brother_physics_engine.update()
		self.sister_physics_engine.update()

		self.engine.update(delta_time, self)

		arcade.set_viewport(
			int(self.controlled.x - SCREEN_WIDTH/2),
			int(self.controlled.x + SCREEN_WIDTH/2),
			int(self.controlled.y - SCREEN_HEIGHT/2),
			int(self.controlled.y + SCREEN_HEIGHT/2),
		)


def main():
	window = Game()
	window.setup()
	arcade.run()


if __name__ == "__main__":
	main()
