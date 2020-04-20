

import arcade

from scale import GLOBAL_SCALE


class Task:


	def update(self, dt, game):

		pass

	def is_alive(self, game):

		pass


class ShortAnimation(Task):


	def __init__(self, x, y, textures_scheme, amount, pace, scale=100/20, corpse=None):

		self.x = x
		self.y = y

		self.textures = [
			arcade.load_texture(textures_scheme.format(str(i)))
			for i in range(1, amount + 1)
		]
		self.pace = pace
		self.index = 0

		self.scale = scale

		self.corpse = corpse

		self.time = 0

	def update(self, dt, game):

		self.time += dt

		if self.time > self.pace/len(self.textures):
			self.index += 1

		if self.index >= len(self.textures):
			return

		self.textures[self.index].draw_scaled(
			center_x=self.x,
			center_y=self.y,
			scale=self.scale,
		)

	def is_alive(self, game):

		if self.index >= len(self.textures):

			if self.corpse is not None:
				game.props.append(self.corpse)

			return False

		return True


class GuideTo(Task):


	def __init__(self, main_entity, x, y, callback=None):

		self.main_entity = main_entity
		self.x = x
		self.y = y
		self.callback = callback

	def update(self, dt, game):

		self.main_entity.set_command(
			self.x - self.main_entity.x,
			self.y - self.main_entity.y,
		)

	def is_alive(self, game):

		if abs(self.main_entity.x - self.x) < 12*GLOBAL_SCALE\
			and abs(self.main_entity.y - self.y) < 12*GLOBAL_SCALE:

			self.main_entity.stop_motion_command()
			if self.callback is not None: self.callback()
			return False

		return True
