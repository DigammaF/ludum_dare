

import arcade, math, random

import task

from scale import GLOBAL_SCALE


ATTACK_TIME = 3
FIST_DAMAGE = 5
STICK_DAMAGE = 20
AXE_DAMAGE = 40
ATTACK_RANGE = 40*GLOBAL_SCALE

BROTHER_BERSERK_DECREASE_RANGE = 80*GLOBAL_SCALE
BROTHER_BERSERK_INCREASE_RANGE = 40*GLOBAL_SCALE
BROTHER_BERSERK_D = 0.1
BROTHER_BERSERK_RND = 0.1
BROTHER_MOOD_TRIAL_TTL = 6

SISTER_PANIC_INCREASE_RANGE = 80*GLOBAL_SCALE
SISTER_PANIC_DECREASE_RANGE = 40*GLOBAL_SCALE
SISTER_PANIC_D = 0.1

BROTHER_SPEED = 20*GLOBAL_SCALE
SISTER_SPEED = 0.9*BROTHER_SPEED
SOLDIER_SPEED = 1.1*BROTHER_SPEED

S_DEMON_TIME = 3
DEMON_TIME = 6
DEMON_DECAY_TIME = 6


def rotated_angle(x, y, r):

	ca = math.cos(r)
	sa = math.sin(r)

	return (ca*x - sa*y, sa*x + ca*y)

def added(v1, v2):
	return (v1[0] + v2[0], v1[1] + v2[1])

def multiplied(v, f):
	return (v[0]*f, v[1]*f)


class MainEntity:


	BROTHER = 0
	SISTER = 1
	SOLDIER = 2


	def __init__(self, x, y, dx, dy, command_x, command_y, level,
				 command_take_weapon, kind, speed=None, dead=False, health=100,
				 has_stick=False, has_axe=False):

		self.x = x
		self.y = y
		self.dx = dx
		self.dy = dy
		self.command_x = command_x
		self.command_y = command_y
		self.level = level # 0-1
		self.has_stick = has_stick
		self.has_axe = has_axe
		self.command_take_weapon = command_take_weapon
		self.kind = kind

		self.associated_exclamation = None
		self.mood_trial_ttl = BROTHER_MOOD_TRIAL_TTL

		self.associated_sprite = None
		self.associated_physics_engine = None

		if speed is None:
			speed = MainEntity.speed_of(kind)

		self.speed = speed

		self.dead = dead
		self.health = health

		self.demon_time = 0
		self.demon_decay_time = DEMON_DECAY_TIME

		self.demon_state = None

		self.display_health_for = 6

		self.can_be_commanded = True

		self.attack_time = 0

		self.pick_weapon_task = None
		self.attack_task = None

	def take_damage(self, d):

		self.health -= d

		if self.health <= 0:
			self.die()

	def computed_damage(self):

		if self.has_axe:
			return AXE_DAMAGE

		if self.has_stick:
			return STICK_DAMAGE

		return FIST_DAMAGE

	def can_attack(self):

		return self.attack_time <= 0

	def try_attack(self, entity):

		if self.can_attack() and arcade.get_distance_between_sprites(self.associated_sprite, entity.associated) <= ATTACK_RANGE:

			self.attack_time = ATTACK_TIME

			entity.take_damage(self.computed_damage())

	@property
	def weapon_t(self):

		if self.has_axe:
			return "axe"

		if self.has_stick:
			return "stick"

		return None

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
			command_take_weapon=False,
			kind=kind,
		)

	def draw_health(self):

		arcade.draw_rectangle_filled(
			center_x=self.x,
			center_y=self.associated_sprite._get_bottom() - GLOBAL_SCALE*10,
			height=GLOBAL_SCALE*3,
			width=(self.health/100)*GLOBAL_SCALE*20,
			color=arcade.csscolor.GREEN,
		)
		arcade.draw_rectangle_outline(
			center_x=self.x,
			center_y=self.associated_sprite._get_bottom() - GLOBAL_SCALE*10,
			height=GLOBAL_SCALE * 3,
			width=GLOBAL_SCALE * 20,
			color=arcade.csscolor.BLACK,
		)

	def get_vision_polygon(self):
		return [
			(self.x, self.y),
			added(rotated_angle(*multiplied((self.dx, self.dy), 66*GLOBAL_SCALE), math.pi/4), (self.x, self.y)),
			added(rotated_angle(*multiplied((self.dx, self.dy), 66*GLOBAL_SCALE), -math.pi/4), (self.x, self.y)),
		 ]

	def draw_vision(self):
		arcade.draw_polygon_outline(self.get_vision_polygon(), arcade.csscolor.GREEN)

	@property
	def is_out_leveled(self):
		return self.level >= 1

	@staticmethod
	def speed_of(kind):
		return {
			MainEntity.BROTHER: BROTHER_SPEED,
			MainEntity.SISTER: SISTER_SPEED,
			MainEntity.SOLDIER: SOLDIER_SPEED,
		}[kind]

	def set_command(self, x, y, speed=None):

		if self.dead: return

		if speed is None:
			speed = self.speed

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

		self.stop_motion_command()
		self.command_take_weapon = False

	def stop_motion_command(self):

		self.command_x = 0
		self.command_y = 0

	def die(self):

		if self.dead: return

		self.associated_sprite.play_die_animation()
		self.dead = True
		self.stop_motion_command()

	def command_take_weapon_off(self):

		self.command_take_weapon = False

	def update_berserk(self, dt, game):

		self.demon_time += dt

		if self.demon_time > S_DEMON_TIME:

			self.demon_state = 1
			self.can_be_commanded = False
			self.stop_motion_command()

		if self.demon_time > DEMON_TIME:

			self.demon_state = 2
			self.can_be_commanded = False

			self.demon_decay_time -= dt

			if self.demon_decay_time < 0:
				self.level = 0
				return

			closest_stick = arcade.get_closest_sprite(self.associated_sprite, game.sticks)
			closest_axe = arcade.get_closest_sprite(self.associated_sprite, game.axes)

			if closest_stick is not None:
				closest_stick, d_stick = closest_stick

			else:
				closest_stick, d_stick = None, float("inf")

			if closest_axe is not None:
				closest_axe, d_axe = closest_axe

			else:
				closest_axe, d_axe = None, float("inf")

			d_sister = arcade.get_distance_between_sprites(self.associated_sprite, game.engine.sister.associated_sprite)

			if self.weapon_t is None:

				if closest_axe is not None and d_axe < d_sister:

					self.command_take_weapon = True

					self.pick_weapon_task = task.XGuideTo(
						entity=self,
						x=closest_axe.center_x,
						y=closest_axe.center_y,
						callback=self.command_take_weapon_off,
					)
					game.add_task(self.pick_weapon_task)

					return

				elif closest_stick is not None and d_stick < d_sister:

					self.command_take_weapon = True

					self.pick_weapon_task = task.XGuideTo(
						entity=self,
						x=closest_stick.center_x,
						y=closest_stick.center_y,
						callback=self.command_take_weapon_off,
					)
					game.add_task(self.pick_weapon_task)

					return

			elif self.weapon_t == "stick":

				if closest_axe is not None and d_axe < d_sister:

					self.command_take_weapon = True

					self.pick_weapon_task = task.XGuideTo(
						entity=self,
						x=closest_axe.center_x,
						y=closest_axe.center_y,
						callback=self.command_take_weapon_off,
					)
					game.add_task(self.pick_weapon_task)

					return

			elif self.weapon_t == "axe":
				pass # nothing to do, already equipped

			self.attack_task = task.AttackMove(entity=self, target=game.engine.sister)
			game.add_task(self.attack_task)

	def reset_berserk(self):

		self.demon_state = None
		self.demon_time = 0
		self.demon_decay_time = DEMON_DECAY_TIME
		self.can_be_commanded = True

		if self.attack_task is not None:
			self.attack_task.quit()

		if self.pick_weapon_task is not None:
			self.pick_weapon_task.quit()

		self.attack_task = None
		self.pick_weapon_task = None

	def try_health_display(self):

		if self.display_health_for > 0:
			self.draw_health()

	def mood_update(self, dt, d, game):

		self.display_health_for = max(0, self.display_health_for - dt)
		self.attack_time = max(-1, self.attack_time - dt)

		if self.dead: return

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

			if self.is_out_leveled:
				self.update_berserk(dt, game)

			else:
				self.reset_berserk()

		elif self.kind == MainEntity.SISTER:

			if d > SISTER_PANIC_INCREASE_RANGE:
				self.level += dt*SISTER_PANIC_D

			if d < SISTER_PANIC_DECREASE_RANGE:
				self.level -= dt*SISTER_PANIC_D

	def manual_update_associated_sprite(self, dt, speed=None):

		if speed is None:
			speed = self.speed

		self.associated_sprite.center_x += self.associated_sprite.change_x*dt*speed
		self.associated_sprite.center_y += self.associated_sprite.change_y*dt*speed

	def update_physics(self):

		self.associated_physics_engine.update()


def distance(e1, e2):
	return math.sqrt((e1.x - e2.x)**2 + (e1.y - e2.y)**2)


class GameEngine:


	def __init__(self, brother: MainEntity, sister: MainEntity, entities):

		self.brother = brother
		self.sister = sister
		self.entities = entities # {key: MainEntity}

	@staticmethod
	def new(brother_x=0, brother_y=0, sister_x=0, sister_y=0):
		return GameEngine(
			brother=MainEntity.new(brother_x, brother_y, MainEntity.BROTHER),
			sister=MainEntity.new(sister_x, sister_y, MainEntity.SISTER),
			entities={},
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

		for e in self.entities.values():
			e.x = e.associated_sprite.center_x
			e.y = e.associated_sprite.center_y
			e.dx = e.associated_sprite.change_x
			e.dy = e.associated_sprite.change_y

		for e in (self.brother, self.sister):
			if e.associated_exclamation is not None:
				e.associated_exclamation.center_x = e.x
				e.associated_exclamation.center_y = e.y

		# Brother and sister mechanics

		if self.brother.command_take_weapon:

			collided_weapons = arcade.check_for_collision_with_list(brother, game.sticks)

			for w in collided_weapons:

				w.remove_from_sprite_lists()
				self.brother.has_stick = True
				break

			collided_weapons = arcade.check_for_collision_with_list(brother, game.axes)

			for w in collided_weapons:

				w.remove_from_sprite_lists()
				self.brother.has_axe = True
				break

		d = distance(self.brother, self.sister)

		self.brother.mood_update(dt, d, game)
		self.sister.mood_update(dt, d, game)

		# End

		brother.change_x = self.brother.computed_dx(dt)
		brother.change_y = self.brother.computed_dy(dt)
		sister.change_x = self.sister.computed_dx(dt)
		sister.change_y = self.sister.computed_dy(dt)

		for e in self.entities.values():

			e.associated_sprite.change_x = e.computed_dx(dt)
			e.associated_sprite.change_y = e.computed_dy(dt)

			#e.manual_update_associated_sprite(dt)
			e.update_physics()
