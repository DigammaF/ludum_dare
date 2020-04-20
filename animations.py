

import arcade


class EntitySprite(arcade.AnimatedTimeBasedSprite):


	def __init__(self,
				 running_right_file_scheme, running_right_amount,
				 idle_right_file_scheme, idle_right_amount,
				 dying_right_file_scheme, dying_right_amount,
				 running_right_pace, idle_pace,
				 dying_right_pace,
				 m_scale,
				 *args, **kwargs):

		super().__init__(*args, **kwargs)

		self.running_right_textures = [
			arcade.load_texture(running_right_file_scheme.format(str(i)))
			for i in range(1, running_right_amount + 1)
		]

		self.running_left_textures = [
			arcade.load_texture(running_right_file_scheme.format(str(i)), mirrored=True)
			for i in range(1, running_right_amount + 1)
		]

		self.idle_right_textures = [
			arcade.load_texture(idle_right_file_scheme.format(str(i)))
			for i in range(1, idle_right_amount + 1)
		]

		self.idle_left_textures = [
			arcade.load_texture(idle_right_file_scheme.format(str(i)), mirrored=True)
			for i in range(1, idle_right_amount + 1)
		]

		self.dying_right_textures = [
			arcade.load_texture(dying_right_file_scheme.format(str(i)))
			for i in range(1, dying_right_amount + 1)
		]

		self.dying_left_textures = [
			arcade.load_texture(dying_right_file_scheme.format(str(i)), mirrored=True)
			for i in range(1, dying_right_amount + 1)
		]

		self.anim_played = self.idle_right_textures
		self.index = 0
		self.time = 0.0
		self.texture = self.idle_right_textures[0]

		self.running = False

		self.running_right_pace = running_right_pace
		self.idle_pace = idle_pace
		self.dying_right_pace = dying_right_pace

		self.running_t = 0
		self.idle_t = 1
		self.dying_t = 2

		self.anim_t = self.idle_t
		self.facing_right = True

		self.paces = {
			self.running_t: self.running_right_pace,
			self.idle_t: self.idle_pace,
			self.dying_t: self.dying_right_pace,
		}

		self.m_scale = m_scale

	def play_die_animation(self):

		self.anim_t = self.dying_t
		self.index = 0
		self.anim_played = [self.dying_right_textures, self.dying_left_textures][not self.facing_right]

	def update_animation(self, delta_time: float = 1/60):

		self._point_list_cache = None
		self.set_hit_box([
			(-8, -20),
			(-8, -5),
			(8, -5),
			(8, -20),
		])

		if self.anim_t == self.dying_t and self.index >= len(self.dying_right_textures):
			return

		self.running = self.change_x != 0 or self.change_y != 0

		self.time += delta_time

		if not self.anim_t == self.dying_t:

			if self.change_x != 0:
				self.facing_right = self.change_x > 0

			if self.running:
				self.anim_t = self.running_t
				self.anim_played = [self.running_left_textures, self.running_right_textures][self.facing_right]

			else:
				self.anim_t = self.idle_t
				self.anim_played = [self.idle_left_textures, self.idle_right_textures][self.facing_right]

		if self.time > self.paces[self.anim_t] / len(self.anim_played):
			self.time = 0
			self.index += 1

		if self.anim_t == self.dying_t and self.index >= len(self.dying_right_textures):
			return

		self.index = self.index%len(self.anim_played)

		self.texture = self.anim_played[self.index]

		"""
		self.texture.hit_box_points = [
			(-10, -15),
			(-5, -20),
			(4, -20),
			(9, -15),
		]
		"""

		self._point_list_cache = None
		self.set_hit_box([
			(-8, -20),
			(-8, -5),
			(8, -5),
			(8, -20),
		])
