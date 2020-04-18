

import arcade, math


BROTHER_BERSERK_DECREASE_RANGE = 400
BROTHER_BERSERK_INCREASE_RANGE = 200
BROTHER_BERSERK_D = 0.1

SISTER_PANIC_INCREASE_RANGE = 400
SISTER_PANIC_DECREASE_RANGE = 200
SISTER_PANIC_D = 0.1


class MainEntity:


	def __init__(self, x, y, dx, dy, command_x, command_y, level, has_weapon):

		self.x = x
		self.y = y
		self.dx = dx
		self.dy = dy
		self.command_x = command_x
		self.command_y = command_y
		self.level = level # 0-1
		self.has_weapon = has_weapon

	@staticmethod
	def new(x, y):
		return MainEntity(
			x=x,
			y=y,
			dx=0,
			dy=0,
			command_x=0,
			command_y=0,
			level=0,
			has_weapon=False,
		)

	@property
	def is_out_leveled(self):
		return self.level >= 1

	def set_command(self, x, y, speed):

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


def distance(e1, e2):
	return math.sqrt((e1.x - e2.x)**2 + (e1.y - e2.y)**2)


class GameEngine:


	def __init__(self, brother: MainEntity, sister: MainEntity):

		self.brother = brother
		self.sister = sister

	@staticmethod
	def new(brother_x=0, brother_y=0, sister_x=0, sister_y=0):
		return GameEngine(
			brother=MainEntity.new(brother_x, brother_y),
			sister=MainEntity.new(sister_x, sister_y),
		)

	def update_brother_berserk(self):

		pass

	def update(self, dt, brother: arcade.Sprite, sister: arcade.Sprite):

		self.brother.x = brother.center_x
		self.brother.y = brother.center_y
		self.brother.dx = brother.change_x
		self.brother.dy = brother.change_y

		self.sister.x = sister.center_x
		self.sister.y = sister.center_y
		self.sister.dx = sister.change_x
		self.sister.dy = sister.change_y

		# Brother and sister mechanics

		if self.brother.is_out_leveled:
			self.update_brother_berserk()

		d = distance(self.brother, self.sister)

		if d > BROTHER_BERSERK_DECREASE_RANGE:
			self.brother.level -= dt*BROTHER_BERSERK_D

		if d < BROTHER_BERSERK_INCREASE_RANGE:
			self.brother.level += dt*BROTHER_BERSERK_D

		if d > SISTER_PANIC_INCREASE_RANGE:
			self.sister.level += dt*SISTER_PANIC_D

		if d < SISTER_PANIC_DECREASE_RANGE:
			self.sister.level -= dt*SISTER_PANIC_D

		# End

		brother.change_x = self.brother.computed_dx(dt)
		brother.change_y = self.brother.computed_dy(dt)
		sister.change_x = self.sister.computed_dx(dt)
		sister.change_y = self.sister.computed_dy(dt)
