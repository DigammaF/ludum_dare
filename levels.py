

import task, arcade, random

from scale import GLOBAL_SCALE


SOLDIER_RELOAD = 3


class Level:


	def setup(self, game):

		pass

	def update(self, dt):

		pass


class LevelOneOld(Level):


	STATE_PATROL = 0
	STATE_HUNT = 1


	class Detection(task.Task):


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


	def setup(self, game):

		sprites = arcade.tilemap.process_layer(game.map, "detect", GLOBAL_SCALE)
		sprite = sprites[0]

		game.add_task(LevelOneOld.Detection(
			sprite=sprite,
			time=10,
			callback=lambda s=self: s.player_house_exit(),
		))

		sprites = arcade.tilemap.process_layer(game.map, "src", GLOBAL_SCALE)
		sprite = sprites[0]

		self.spawn_soldiers = sprite

		sprites = arcade.tilemap.process_layer(game.map, "dst", GLOBAL_SCALE)
		sprite = sprites[0]

		self.house_front = sprite

		self.patrols = arcade.tilemap.process_layer(game.map, "search", GLOBAL_SCALE)

		for i in range(len(self.patrols)):
			self.patrols[i].last_visit_time = 0

		self.game = game
		self.keys = []

	def update(self, dt):

		for patrol in self.patrols:
			patrol.last_visit_time += dt

		for key in self.keys:

			entity = self.game.engine.entities[key]
			entity.reload -= dt

	def player_house_exit(self):

		print("Spawn")

		for _ in range(3):

			key = self.game.add_entity(
				self.game.new_entity(
					self.spawn_soldiers.center_x,
					self.spawn_soldiers.center_y,
					self.game.ENTITY_KIND_SOLDIER,
				),
				self.game.new_solider_animated_sprite(),
			)

			self.keys.append(key)

			entity = self.game.engine.entities[key]

			entity.state = LevelOneOld.STATE_PATROL
			entity.reload = SOLDIER_RELOAD

			self.game.add_task(task.After(1, lambda self=self, entity=entity:
			self.game.add_task(task.GuideTo(
				main_entity=entity,
				x=entity.x + random.randint(160*GLOBAL_SCALE, 320*GLOBAL_SCALE),
				y=entity.y + random.randint(-20*GLOBAL_SCALE, 80*GLOBAL_SCALE),
				callback=lambda s=self, e=entity, g=self.game: s.soldier_go_to_house(e, g),
				stop_when=lambda ss=self, e=entity: ss.are_children_located(e),
			))
							   ))

	def soldier_go_to_house(self, entity, game):

		patrol = self.patrols[random.randint(0, len(self.patrols) - 1)]

		game.add_task(task.After(1, lambda self=self, entity=entity, game=game:
		game.add_task(task.GuideTo(
			main_entity=entity,
			x=self.house_front.center_x,
			y=self.house_front.center_y,
			callback=lambda s=self, e=entity, g=game, p=patrol: g.add_task((task.GuideTo(
				main_entity=e,
				x=p.center_x,
				y=p.center_y,
				callback=lambda s=self, e=e, g=g: s.take_soldier_on_patrol(e, g),
				stop_when=lambda ss=self, e=entity: ss.are_children_located(e),
			))),
			stop_when=lambda ss=self, e=entity: ss.are_children_located(e),
		))
								 ))

	def take_soldier_on_patrol(self, entity, game):

		m = float("-inf")
		patrol = None

		for p in self.patrols:

			if p.last_visit_time > m:
				m = p.last_visit_time
				patrol = p

		patrol.last_visit_time = 0

		game.add_task(task.After(1, lambda entity=entity, game=game:
		game.add_task(task.GuideTo(
			main_entity=entity,
			x=patrol.center_x,
			y=patrol.center_y,
			callback=lambda s=self, e=entity, g=game: s.take_soldier_on_patrol(e, g),
			stop_when=lambda ss=self, e=entity: ss.are_children_located(e),
		))
								 ))

	def are_children_located(self, soldier):

		for c in (self.game.engine.brother, self.game.engine.sister):

			if self.game.xcan_see(soldier, c):

				print("Located")

				for key in self.keys:
					self.go_hunt(self.game.engine.entities[key], c)

				return True

		return False

	def go_hunt(self, soldier, target):

		self.game.add_task(task.After(1, lambda self=self, soldier=soldier, target=target:
			self.game.add_task(task.GuideTo(
				main_entity=soldier,
				x=target.x,
				y=target.y,
				callback=lambda s=soldier, t=target, ss=self: ss.shoot(s, t),
				stop_when=lambda ss=self, s=soldier: ss.is_hunt_successful(s),
			))
		))

	def is_hunt_successful(self, soldier):

		for c in (self.game.engine.brother, self.game.engine.sister):

			if self.game.xcan_see(soldier, c):

				self.shoot(soldier, c)

				return True

		return False

	def shoot(self, soldier, target):

		if self.game.xcan_see(soldier, target):

			if soldier.reload > 0:
				self.go_hunt(soldier, target)
				return

			self.game.add_task(task.SoldierShot(target.x, target.y))

			soldier.reload = SOLDIER_RELOAD

		self.game.add_task(task.After(1,
			lambda self=self, soldier=soldier:
			self.take_soldier_on_patrol(soldier, self.game)
		))


class LevelOne(Level):

	pass


class LevelTwo(Level):

	pass


class LevelThree(Level):

	pass


class LevelFour(Level):

	pass
