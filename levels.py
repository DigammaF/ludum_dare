

import task, arcade, random


class Level:


	def setup(self, game):

		pass

	def update(self, dt):

		pass


class LevelOne(Level):


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

		sprites = arcade.tilemap.process_layer(game.map, "detect", 100/20)
		sprite = sprites[0]

		game.add_task(LevelOne.Detection(
			sprite=sprite,
			time=10,
			callback=lambda s=self: s.player_house_exit(),
		))

		sprites = arcade.tilemap.process_layer(game.map, "src", 100/20)
		sprite = sprites[0]

		self.spawn_soldiers = sprite

		sprites = arcade.tilemap.process_layer(game.map, "dst", 100/20)
		sprite = sprites[0]

		self.house_front = sprite

		self.patrols = arcade.tilemap.process_layer(game.map, "search", 100/20)

		for i in range(len(self.patrols)):
			self.patrols[i].last_visit_time = 0

		self.game = game
		self.keys = []

	def update(self, dt):

		for patrol in self.patrols:
			patrol.last_visit_time += dt

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

			self.game.add_task(task.GuideTo(
				main_entity=entity,
				x=entity.x + random.randint(800, 1600),
				y=entity.y + random.randint(-100, 400),
				callback=lambda s=self, e=entity, g=self.game: s.soldier_go_to_house(e, g)
			))

	def soldier_go_to_house(self, entity, game):

		patrol = self.patrols[random.randint(0, len(self.patrols) - 1)]

		game.add_task(task.GuideTo(
			main_entity=entity,
			x=self.house_front.center_x,
			y=self.house_front.center_y,
			callback=lambda s=self, e=entity, g=game, p=patrol: g.add_task((task.GuideTo(
				main_entity=e,
				x=p.center_x,
				y=p.center_y,
				callback=lambda s=self, e=e, g=g: s.take_soldier_on_patrol(e, g)
			)))
		))

	def take_soldier_on_patrol(self, entity, game):

		m = float("-inf")
		patrol = None

		for p in self.patrols:

			if p.last_visit_time > m:
				m = p.last_visit_time
				patrol = p

		patrol.last_visit_time = 0

		game.add_task(task.GuideTo(
			main_entity=entity,
			x=patrol.center_x,
			y=patrol.center_y,
			callback=lambda s=self, e=entity, g=game: s.take_soldier_on_patrol(e, g)
		))
