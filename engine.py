

import arcade, math, random


BROTHER_BERSERK_DECREASE_RANGE = 400
BROTHER_BERSERK_INCREASE_RANGE = 200
BROTHER_BERSERK_D = 0.1
BROTHER_BERSERK_RND = 0.1
BROTHER_MOOD_TRIAL_TTL = 6

SISTER_PANIC_INCREASE_RANGE = 400
SISTER_PANIC_DECREASE_RANGE = 200
SISTER_PANIC_D = 0.1

BROTHER_SPEED = 200
SISTER_SPEED = 0.9*BROTHER_SPEED


class MainEntity:


	BROTHER = 0
	SISTER = 1


	def __init__(self, x, y, dx, dy, command_x, command_y, level, has_weapon,
				 command_take_weapon, kind):

		self.x = x
		self.y = y
		self.dx = dx
		self.dy = dy
		self.command_x = command_x
		self.command_y = command_y
		self.level = level # 0-1
		self.has_weapon = has_weapon
		self.command_take_weapon = command_take_weapon
		self.kind = kind

		self.associated_exclamation = None
		self.mood_trial_ttl = BROTHER_MOOD_TRIAL_TTL

	@staticmethod
	def new(x, y, kind):
		return MainEntity(
			x=x,
			y=y,
			dx=0,
			dy=0,
			command_x=0,
			command_y=0,
			level=0,
			has_weapon=False,
			command_take_weapon=False,
			kind=kind,
		)

	@property
	def is_out_leveled(self):
		return self.level >= 1

	@staticmethod
	def speed_of(kind):
		return {
			MainEntity.BROTHER: BROTHER_SPEED,
			MainEntity.SISTER: SISTER_SPEED,
		}[kind]

	def set_command(self, x, y, speed=None):

		if speed is None:
			speed = MainEntity.speed_of(self.kind)

		l = math.sqrt(x**2 + y**2)

		if l == 0:

			self.command_x = 0
			self.command_y = 0

			return

		self.command_x = x * speed/l
		self.command_y = y * speed/l

	def computed_dx(self, dt):

		return self.command_x*dt

	def computed_dy(self, dt):

		return self.command_y*dt

	def stop_commands(self):

		self.command_x = 0
		self.command_y = 0
		self.command_take_weapon = False

	def mood_update(self, dt, d):

		if self.kind == MainEntity.BROTHER:

			if d > BROTHER_BERSERK_DECREASE_RANGE:
				self.level -= dt*BROTHER_BERSERK_D

			else:

				self.level += random.random()*BROTHER_BERSERK_RND*dt

			self.mood_trial_ttl -= dt

			if self.mood_trial_ttl <= 0:

				self.mood_trial_ttl = BROTHER_MOOD_TRIAL_TTL

				if max(self.level, 0.1) > random.random():
					self.level += 1

		elif self.kind == MainEntity.SISTER:

			if d > SISTER_PANIC_INCREASE_RANGE:
				self.level += dt*SISTER_PANIC_D

			if d < SISTER_PANIC_DECREASE_RANGE:
				self.level -= dt*SISTER_PANIC_D


def distance(e1, e2):
	return math.sqrt((e1.x - e2.x)**2 + (e1.y - e2.y)**2)


class GameEngine:


	def __init__(self, brother: MainEntity, sister: MainEntity):

		self.brother = brother
		self.sister = sister

	@staticmethod
	def new(brother_x=0, brother_y=0, sister_x=0, sister_y=0):
		return GameEngine(
			brother=MainEntity.new(brother_x, brother_y, MainEntity.BROTHER),
			sister=MainEntity.new(sister_x, sister_y, MainEntity.SISTER),
		)

	def update_brother_berserk(self):

		pass

	def update_sister_panicked(self):

		pass

	def update(self, dt, game):

		brother = game.brother
		sister = game.sister

		self.brother.x = brother.center_x
		self.brother.y = brother.center_y
		self.brother.dx = brother.change_x
		self.brother.dy = brother.change_y

		self.sister.x = sister.center_x
		self.sister.y = sister.center_y
		self.sister.dx = sister.change_x
		self.sister.dy = sister.change_y

		for e in (self.brother, self.sister):
			if e.associated_exclamation is not None:
				e.associated_exclamation.center_x = e.x
				e.associated_exclamation.center_y = e.y

		# Brother and sister mechanics

		if self.brother.command_take_weapon:

			collided_weapons = arcade.check_for_collision_with_list(brother, game.weapons)

			for w in collided_weapons:

				w.remove_from_sprite_lists()
				self.brother.has_weapon = True
				break

		if self.brother.is_out_leveled:
			self.update_brother_berserk()

		d = distance(self.brother, self.sister)

		self.brother.mood_update(dt, d)
		self.sister.mood_update(dt, d)

		# End

		brother.change_x = self.brother.computed_dx(dt)
		brother.change_y = self.brother.computed_dy(dt)
		sister.change_x = self.sister.computed_dx(dt)
		sister.change_y = self.sister.computed_dy(dt)
