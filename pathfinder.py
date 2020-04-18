

import arcade, math

from queue import SimpleQueue


class Tree:


	def __init__(self, nodes):

		self.nodes = nodes
		self.poly = None

	def destroy_route(self, key):

		for node in self.nodes:

			if key in node.safe:
				del node.safe[key]

	def can_try_to_create_route(self, x, y, x_dst, y_dst):

		return arcade.is_point_in_polygon(x, y, self.poly)\
			and arcade.is_point_in_polygon(x_dst, y_dst, self.poly)

	@staticmethod
	def generate(game):

		nodes = []
		cart_map = {} # {(int, int): bool} (bool: is it a wall?)
		nodes_map = {} # {(int, int): node}

		for ground_sprite in game.grounds:

			nodes.append(Node.new(
				x=ground_sprite.center_x,
				y=ground_sprite.center_y,
			))

			reduced_coord = (
				ground_sprite.center_x//game.TILE_SIZE,
				ground_sprite.center_y//game.TILE_SIZE,
			)

			nodes_map[reduced_coord] = nodes[-1]

			if arcade.get_sprites_at_point(
				[
					ground_sprite.center_x,
					ground_sprite.center_y,
				],
				game.walls,
			):
				cart_map[reduced_coord] = True

			else:
				cart_map[reduced_coord] = False

		for coord, node in cart_map.items():

			for vicinity_coord in (
				(coord[0] + 1, coord[1]),
				(coord[0] - 1, coord[1]),
				(coord[0], coord[1] + 1),
				(coord[0], coord[1] - 1),
			):

				if vicinity_coord in cart_map:
					if not cart_map[vicinity_coord]:
						nodes_map[coord].link_to(nodes_map[vicinity_coord])

		return Tree(nodes=nodes)


class Node:


	def __init__(self, links, safe, x, y):

		self.links = links # {local_index(int): Node}
		self.safe = safe # {int: {"height": int}
		self.x = x
		self.y = y

	@staticmethod
	def new(x, y):
		return Node(
			links={},
			safe={},
			x=x,
			y=y,
		)

	def link_to(self, node):

		index = 0

		while index in self.links:
			index += 1

		self.links[index] = node

	def least_surrounding_height(self, key):

		m = float("inf")

		for node in self.links.values():

			h = node.safe.get(key, {"height": float("inf")})["height"]
			if h < m: m = h

		return m

	def lower_surrounding_local_index(self, key):

		m = float("inf")
		i = None

		for index, node in self.links.items():

			h = node.safe.get(key, {"height": float("inf")})["height"]

			if h < m:

				m = h
				i = index

		return i


def create_route(src, dst, index_pool):
	"""

	return key, found

	:param src:
	:param dst:
	:param index_pool:
	:return:
	"""

	key = index_pool.create()

	tagged = set()
	left_to_tag = SimpleQueue()

	found = False

	dst.safe[key] = {
		"height": 0,
	}

	tagged.add(dst)

	for node in dst.links.values():
		tagged.add(node)
		left_to_tag.put_nowait(node)

	while (not found) and (not left_to_tag.empty()):

		node = left_to_tag.get_nowait()

		if node is src:
			found = True

		node.safe[key] = {
			"height": node.least_surrounding_height(key) + 1,
		}

		for sub_node in node.links.values():

			if sub_node not in tagged:
				tagged.add(sub_node)
				left_to_tag.put_nowait(sub_node)

	return key, found


def create_route_points(src_x, src_y, dst_x, dst_y, index_pool, game):

	points = []

	m_src = float("inf")
	nearest_node_src = None
	m_dst = float("inf")
	nearest_node_dst = None

	for node in game.pf_tree.nodes:

		d_src = math.sqrt((src_x - node.x)**2 + (src_y - node.y)**2)
		d_dst = math.sqrt((dst_x - node.x)**2 + (dst_y - node.y)**2)

		if d_src < m_src:

			m_src = d_src
			nearest_node_src = node

		if d_dst < m_dst:

			m_dst = d_dst
			nearest_node_dst = node

	key, found = create_route(nearest_node_src, nearest_node_dst, index_pool)

	if not found: return None, key

	points.append((nearest_node_src.x, nearest_node_src.y))

	current_node = nearest_node_src

	while current_node is not nearest_node_dst:

		next_index = current_node.lower_surrounding_local_index(key)
		current_node = current_node.links[next_index]
		points.append((current_node.x, current_node.y))

	points.append((dst_x, dst_y))

	return points, key


class IndexPool:


	def __init__(self, indexes):

		self.indexes = indexes

	@staticmethod
	def new():
		return IndexPool(indexes=set())

	def create(self):

		i = 0

		while i in self.indexes:
			i += 1

		self.indexes.add(i)

		return i

	def destroy(self, index):

		self.indexes.remove(index)
