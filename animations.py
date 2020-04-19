

import arcade


class EntitySprite(arcade.AnimatedTimeBasedSprite):


	def __init__(self,
				 running_right_file_scheme, running_right_amount,
				 idle_file_scheme, idle_amount,
				 running_right_pace, idle_pace,
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

		self.idle_textures = [
			arcade.load_texture(idle_file_scheme.format(str(i)))
			for i in range(1, idle_amount + 1)
		]

		self.anim_played = self.idle_textures
		self.index = 0
		self.time = 0.0
		self.texture = self.idle_textures[0]

		self.running = False

		self.running_right_pace = running_right_pace
		self.idle_pace = idle_pace

		self.running_t = 0
		self.idle_t = 1

		self.anim_t = self.idle_t

		self.paces = {
			self.running_t: self.running_right_pace,
			self.idle_t: self.idle_pace,
		}

		self.m_scale = m_scale

	def update_animation(self, delta_time: float = 1/60):

		self.running = self.change_x != 0 or self.change_y != 0

		self.time += delta_time

		if self.running:
			self.anim_t = self.running_t
			self.anim_played = [self.running_right_textures, self.running_left_textures][self.change_x < 0]

		else:
			self.anim_t = self.idle_t
			self.anim_played = self.idle_textures

		if self.time > self.paces[self.anim_t] / len(self.anim_played):
			self.time = 0
			self.index += 1

		self.index = self.index%len(self.anim_played)

		self.texture = self.anim_played[self.index]
