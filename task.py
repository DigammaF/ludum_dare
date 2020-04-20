

import random

import arcade

from pathlib import Path

from scale import GLOBAL_SCALE


class Task:


	def setup(self, game):

		pass

	def update(self, dt, game):

		pass

	def is_alive(self, game):

		pass


class Animator(arcade.AnimatedTimeBasedSprite):


	def __init__(self, textures_scheme, amount, pace, scale, *args, **kwargs):

		super().__init__(*args, **kwargs)

		self.textures = [
			arcade.load_texture(textures_scheme.format(str(i)))
			for i in range(1, amount + 1)
		]

		self.index = 0
		self.pace = pace
		self.time = 0
		self.m_scale = scale

	def update_animation(self, delta_time: float = 1/60):

		self.time += delta_time

		if self.time > self.pace/len(self.textures):

			self.index += 1
			self.time = 0

		if self.index >= len(self.textures):
			return

		self.texture = self.textures[self.index]

	def is_done(self):
		return self.index >= len(self.textures)


class ShortAnimation(Task):


	def __init__(self, x, y, textures_scheme, amount, pace, scale=GLOBAL_SCALE, corpse=None):

		self.x = x
		self.y = y

		self.animator = Animator(textures_scheme=textures_scheme, amount=amount, pace=pace, scale=scale)

		self.corpse = corpse

	def setup(self, game):

		game.animators.append(self.animator)
		self.animator.center_x = self.x
		self.animator.center_y = self.y

	def update(self, dt, game):

		self.animator.update_animation(dt)

	def is_alive(self, game):

		if self.animator.is_done():

			self.animator.remove_from_sprite_lists()

			if self.corpse is not None:
				game.props.append(self.corpse)

			return False

		return True


def if_exe(cond, f):

	if cond():
		f()


class XGuideTo(Task):


	def __init__(self, entity, x, y, callback=None):

		self.entity = entity
		self.x = x
		self.y = y

		self.route_points = None
		self.key = None
		self.keep_alive = True

		self.callback = callback

		self.last_created_motion_task_key = None

	def setup(self, game):

		self.route_points, self.key = game.create_route_points(
			self.entity.x,
			self.entity.y,
			self.x,
			self.y,
		)

		self.game = game

		if self.route_points is None:
			return

		self.follow_path()

	def quit(self):

		self.entity.stop_motion_command("XGuideTo.quit")
		self.game.pf_tree.destroy_route(self.key)
		self.keep_alive = False

	def update(self, dt, game):

		r = arcade.get_closest_sprite(self.entity.associated_sprite, game.doors)

		if r is not None:

			d = r[1]

			if d <= game.DOOR_INTERACTION_RANGE:
				game.entity_switch_door(self.entity)

	def follow_path(self):

		if not self.route_points:
			self.quit()
			return

		gogoal = self.route_points[0]
		del self.route_points[0]

		self.game.add_task(GuideTo(
			main_entity=self.entity,
			x=gogoal[0],
			y=gogoal[1],
			callback=lambda self=self: if_exe(
				lambda self=self: self.keep_alive,
				self.follow_path
			),
		))

	def is_alive(self, game):
		return self.keep_alive


class PermaFollow(Task):


	def __init__(self, follower, followed, stop_when):

		self.follower = follower
		self.followed = followed

		self.followed_coord = (self.followed.x, self.followed.y)

		self.stop_when = stop_when

		self.guider = None
		self.guider_key = None

		self.keep_alive = True
		self.pause = False

	def update(self, dt, game):

		if self.stop_when():
			self.quit()
			return

		if abs(self.followed.x - self.followed_coord[0]) > 20*GLOBAL_SCALE\
			or abs(self.followed.y - self.followed_coord[1]) > 20*GLOBAL_SCALE:
			self.drop_guider()

		self.pause = abs(self.followed.x - self.follower.x) < 20*GLOBAL_SCALE\
		and abs(self.followed.y - self.follower.y) < 20*GLOBAL_SCALE

		if self.pause:
			self.drop_guider()

		if self.guider is None and not self.pause:

			self.guider = XGuideTo(self.follower, self.followed.x, self.followed.y,
								   callback=self.drop_guider)
			self.guider_key = game.add_task(self.guider)

	def quit(self):

		if self.guider is not None:
			self.guider.quit()

		self.keep_alive = False

	def drop_guider(self):

		if self.guider is not None:
			self.guider.quit()

		self.guider = None

	def is_alive(self, game):

		return self.keep_alive


class AttackMove(Task):


	def __init__(self, entity, target):

		self.entity = entity
		self.target = target

		self.guider = None

		self.keep_alive = True

	def update(self, dt, game):

		self.entity.try_attack(self.target)

		if not self.keep_alive:
			return

		if self.guider is None:

			self.guider = PermaFollow(followed=self.target, follower=self.entity, stop_when=lambda :False)
			game.add_task(self.guider)

	def quit(self):

		if self.guider is not None:
			self.guider.quit()

		self.keep_alive = False

	def is_alive(self, game):
		return self.keep_alive


class Hunt(Task):


	def __init__(self, hunter):

		self.hunter = hunter

	def update(self, dt, game):

		for e in (game.engine.brother, game.engine.sister):
			game.try_shoot(self.hunter, e)

	def is_alive(self, game):
		return True


class GuideTo(Task):


	def __init__(self, main_entity, x, y, callback=None, stop_when=None):

		self.main_entity = main_entity
		self.x = x
		self.y = y
		self.callback = callback
		self.stop_when = stop_when

		self.broke = False

	def update(self, dt, game):

		if self.stop_when is not None:
			if self.stop_when():
				self.broke = True
				return

		self.main_entity.set_command(
			self.x - self.main_entity.x,
			self.y - self.main_entity.y,
		)

	def is_alive(self, game):

		if self.broke:
			self.main_entity.stop_motion_command("GuideTo.is_alive 1")
			return False

		if abs(self.main_entity.x - self.x) < 12*GLOBAL_SCALE\
			and abs(self.main_entity.y - self.y) < 12*GLOBAL_SCALE:

			self.main_entity.stop_motion_command("GuideTO.is_alive 2")
			if self.callback is not None: self.callback()
			return False

		return True


class After(Task):


	def __init__(self, time, f):

		self.time = time
		self.f = f

	def update(self, dt, game):

		self.time -= dt

	def is_alive(self, game):

		if self.time < 0:

			self.f()
			return False

		return True


class SoldierShot(Task):


	RND = 10*GLOBAL_SCALE


	def __init__(self, x, y, rnd=True):

		self.x = x
		self.y = y

		self.rnd = rnd

	def is_alive(self, game):

		if self.rnd:

			self.x += random.random()*SoldierShot.RND - 0.5*SoldierShot.RND
			self.y += random.random()*SoldierShot.RND - 0.5*SoldierShot.RND

		game.add_task(After(0.1, lambda self=self, game=game:
							game.add_task(ShortAnimation(
								textures_scheme=str(Path("assets")/"animations"/"bullet_impact_{}.png"),
								amount=3,
								pace=0.2,
								x=self.x,
								y=self.y,
							))
							))

		if arcade.is_point_in_polygon(self.x, self.y, game.brother.points):
			game.engine.brother.die()

		if arcade.is_point_in_polygon(self.x, self.y, game.sister.points):
			game.engine.sister.die()

		return False


class Die(Task):


	def __init__(self, entity):

		self.entity = entity

	def is_alive(self, game):

		self.entity.die()
		return False


class Detection(Task):


	def __init__(self, sprite, time, callback):

		self.sprite = sprite

		self.pre_triggered = False
		self.triggered = False

		self.time = time
		self.callback = callback

	def update(self, dt, game):

		if arcade.are_polygons_intersecting(self.sprite.points, game.brother.points)\
			or arcade.are_polygons_intersecting(self.sprite.points, game.sister.points):
			self.pre_triggered = True

		if self.pre_triggered:

			self.time -= dt

			if self.time <= 0:
				self.triggered = True

	def is_alive(self, game):

		if self.triggered:

			self.callback()
			return False

		return True


class SoundPlayer(Task):


	pass
