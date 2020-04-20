

import arcade


class EntitySprite(arcade.AnimatedTimeBasedSprite):


	def __init__(self,
				 running_right_file_scheme, running_right_amount,
				 idle_right_file_scheme, idle_right_amount,
				 dying_right_file_scheme, dying_right_amount,
				 running_right_pace, idle_pace,
				 dying_right_pace,
				 m_scale,
				 running_right_s_demon_scheme=None,
				 running_right_s_demon_amount=None,
				 running_right_s_demon_pace=None,
				 running_right_demon_scheme=None,
				 running_right_demon_amount=None,
				 running_right_demon_pace=None,
				 running_right_demon_stick_scheme=None,
				 running_right_demon_stick_amount=None,
				 running_right_demon_stick_pace=None,
				 running_right_demon_axe_scheme=None,
				 running_right_demon_axe_amount=None,
				 running_right_demon_axe_pace=None,
				 kind=None,
				 *args, **kwargs):

		super().__init__(*args, **kwargs)

		self.kind = kind

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

		if running_right_s_demon_scheme is not None:

			self.running_right_s_demon_textures = [
				arcade.load_texture(running_right_s_demon_scheme.format(str(i)))
				for i in range(1, running_right_s_demon_amount + 1)
			]

			self.running_left_s_demon_textures = [
				arcade.load_texture(running_right_s_demon_scheme.format(str(i)), mirrored=True)
				for i in range(1, running_right_s_demon_amount + 1)
			]

			self.running_right_demon_textures = [
				arcade.load_texture(running_right_demon_scheme.format(str(i)))
				for i in range(1, running_right_demon_amount + 1)
			]

			self.running_left_demon_textures = [
				arcade.load_texture(running_right_demon_scheme.format(str(i)), mirrored=True)
				for i in range(1, running_right_demon_amount + 1)
			]

			self.running_right_demon_stick_textures = [
				arcade.load_texture(running_right_demon_stick_scheme.format(str(i)))
				for i in range(1, running_right_demon_stick_amount + 1)
			]

			self.running_left_demon_stick_textures = [
				arcade.load_texture(running_right_demon_stick_scheme.format(str(i)), mirrored=True)
				for i in range(1, running_right_demon_stick_amount + 1)
			]

			self.running_right_demon_axe_textures = [
				arcade.load_texture(running_right_demon_axe_scheme.format(str(i)))
				for i in range(1, running_right_demon_axe_amount + 1)
			]

			self.running_left_demon_axe_textures = [
				arcade.load_texture(running_right_demon_axe_scheme.format(str(i)), mirrored=True)
				for i in range(1, running_right_demon_axe_amount + 1)
			]

		self.anim_played = self.idle_right_textures
		self.index = 0
		self.time = 0.0
		self.texture = self.idle_right_textures[0]

		self.running = False

		self.running_right_pace = running_right_pace
		self.idle_pace = idle_pace
		self.dying_right_pace = dying_right_pace
		self.running_right_s_demon_pace = running_right_s_demon_pace
		self.running_right_demon_pace = running_right_demon_pace
		self.running_right_demon_stick_pace = running_right_demon_stick_pace
		self.running_right_demon_axe_pace = running_right_demon_axe_pace

		self.running_t = 0
		self.idle_t = 1
		self.dying_t = 2
		self.running_s_demon_t = 3
		self.running_demon_t = 4
		self.running_demon_stick_t = 5
		self.running_demon_axe_t = 6

		self.anim_t = self.idle_t
		self.facing_right = True

		self.paces = {
			self.running_t: self.running_right_pace,
			self.idle_t: self.idle_pace,
			self.dying_t: self.dying_right_pace,
			self.running_s_demon_t: self.running_right_s_demon_pace,
			self.running_demon_t: self.running_right_demon_pace,
			self.running_demon_stick_t: self.running_right_demon_stick_pace,
			self.running_demon_axe_t: self.running_right_demon_axe_pace,
		}

		self.m_scale = m_scale

		self.demon_state = None
		self.weapon = None

	def play_die_animation(self):

		self.anim_t = self.dying_t
		self.index = 0
		self.anim_played = [self.dying_right_textures, self.dying_left_textures][not self.facing_right]

	def update_animation(self, delta_time: float = 1/60):

		#demon_state = 0|1|2
		#weapon = None|'stick'|'axe'

		demon_state = self.demon_state
		weapon = self.weapon

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

			if self.running or (demon_state != None and demon_state != 0):

				if demon_state is None or demon_state == 0:

					self.anim_t = self.running_t
					self.anim_played = [self.running_left_textures, self.running_right_textures][self.facing_right]

				elif demon_state == 1:

					self.anim_t = self.running_s_demon_t
					self.anim_played = [self.running_left_s_demon_textures , self.running_right_s_demon_textures][self.facing_right]

				elif demon_state == 2:

					if weapon is None:

						self.anim_t = self.running_demon_t
						self.anim_played = [self.running_left_demon_textures, self.running_right_demon_textures][self.facing_right]

					elif weapon == "stick":

						self.anim_t = self.running_demon_stick_t
						self.anim_played = [self.running_left_demon_stick_textures, self.running_right_demon_stick_textures][self.facing_right]

					elif weapon == "axe":

						self.anim_t = self.running_demon_axe_t
						self.anim_played = [self.running_left_demon_axe_textures, self.running_right_demon_axe_textures][self.facing_right]

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
