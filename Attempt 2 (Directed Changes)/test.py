import numpy as np
import tkinter as tk
from datetime import datetime
import copy
import os
import matplotlib as mpl
import matplotlib.pyplot as plt

plt.ion()

print("space - toggle visibility\nbackspace - toggle graph of output values")

## classes
# screen class
class screen:
	"""Handles the creation of the screen and obstacles."""
	def __init__(self, amount_of_players = 1, start_scroll_speed = 6, max_scroll_speed = 50, save_folder = "trained_model", save_name = "1"):
		# variables
		self.amount_of_players = amount_of_players

		self.scroll_speed = start_scroll_speed
		self.max_scroll_speed = max_scroll_speed

		self.canvas_width = 1200
		self.canvas_height = 600
		self.ground_height = 100
		self.ground_y_value = self.canvas_height - self.ground_height

		self.obstacles = np.array([[-1, 200, -1, 200, -1]]) # [[tkinter shape, x1, y1, x2, y2], ...]; we set this to -1 200 -1 200 -1 because we need an initial x value to base our initial obstacles' x values off of
		self.distance = 0

		self.alive_players = np.array([]) # [player, ...]
		self.dead_players = np.empty((0, 2)) # [[player, dist before death], ...]

		self.save_folder = save_folder
		self.save_name = save_name



	def create(self):
		# create the window
		self.root = tk.Tk()
		self.canvas = tk.Canvas(self.root, bg="sky blue", height=self.canvas_height, width=self.canvas_width)
		self.root.title("Dinosaur game")
		self.canvas.pack()

		# create the ground
		self.ground = self.canvas.create_rectangle((0 - 10, self.canvas_height + 10), (self.canvas_width + 10, self.ground_y_value), fill="lawn green", outline="brown", width = 4)

		# fill screen with obstacles
		for _ in range(5):
			self.obstacles = np.append(self.obstacles, [self.create_obstacle()], axis = 0)

		self.obstacles = self.obstacles[1::]

		# create the players
		for _ in range(self.amount_of_players):
			self.alive_players = np.append(self.alive_players, player_class(self))
			if render: self.alive_players[-1].render()


	def recreate(self):
		self.canvas.delete("all")
		self.canvas.pack()

		self.ground = self.canvas.create_rectangle((0 - 10, self.canvas_height + 10), (self.canvas_width + 10, self.ground_y_value), fill="lawn green", outline="brown", width = 4)

		# fill screen with obstacles
		for _ in range(5):
			self.obstacles = np.append(self.obstacles, [self.create_obstacle()], axis = 0)

		self.obstacles = self.obstacles[1::]

		for player in self.alive_players:
			player.x = np.random.random() * 100 + 50
			player.y = player.game.ground_y_value
			player.vy = 0
			player.h = 50
			player.state = 0
			if render: player.render()


	def create_obstacle(self, ground_probability = 0.8):
		if np.random.random() < ground_probability:
			width = 60 + (2*np.random.random() - 1) * 15 # (center value + scale factor) + rand(-1 --> 1) * (variance + scale factor)
			height = 55**2 / width
			last_x = self.obstacles[-1, 3]
			gap = 60 * np.random.random() + 100 + self.scroll_speed * 5 + width # rand * variance + min. dist + scale factor

			x1, y1, x2, y2 = last_x + gap, self.ground_y_value, last_x + gap + width, self.ground_y_value - height

			if render:
				return self.canvas.create_rectangle((x1, y1), (x2, y2), fill="green", outline="", tag = "obstacle"), last_x + gap, self.ground_y_value, last_x + gap + width, self.ground_y_value - height
			return None, x1, y1, x2, y2
		else:
			width = 40
			height = 40
			altitude = np.random.random() * 100 + 15 # rand * variance + min. height
			last_x = self.obstacles[-1, 3]
			gap = 60 * np.random.random() + 100 + self.scroll_speed * 5 # rand * variance + min. dist + scale factor

			x1, y1, x2, y2 = last_x + gap, self.ground_y_value - altitude, last_x + gap + width, self.ground_y_value - altitude - height

			if render:
				self.canvas.create_rectangle((x1, y1), (x2, y2), fill="brown", outline="", tag = "obstacle"), last_x + gap, self.ground_y_value - altitude, last_x + gap + width, self.ground_y_value - altitude - height
			return None, x1, y1, x2, y2


	def render_obstacles(self):
		for index, (_, x1, y1, x2, y2) in enumerate(self.obstacles):
			if y1 == self.ground_y_value:
				self.obstacles[index][0] = self.canvas.create_rectangle((x1, y1), (x2, y2), fill="green", outline="", tag = "obstacle")
			else:
				self.obstacles[index][0] = self.canvas.create_rectangle((x1, y1), (x2, y2), fill="brown", outline="", tag = "obstacle")


	def remove_out_of_bounds(self):
		"""Removes out of bounds obstacles"""
		obstacles_x2 = self.obstacles[:, 3]

		if np.all(obstacles_x2 >= 0): return

		OOB_obstacles = self.obstacles[obstacles_x2 < 0]

		self.obstacles = self.obstacles[obstacles_x2 >= 0]

		for obstacle in OOB_obstacles:
			self.canvas.delete(obstacle)

		self.obstacles = np.append(self.obstacles, [self.create_obstacle() for obstacle in OOB_obstacles], axis = 0)


	def update(self):
		self.canvas.move('obstacle', -1 * self.scroll_speed, 0)
		self.obstacles[:, [1,3]] -= 1 * self.scroll_speed

		for player in self.alive_players:
			player.update_motion()

		self.remove_out_of_bounds()

		self.scroll_speed += 0.05*(-1/self.max_scroll_speed*self.scroll_speed+1) # [initial rate of change in speed per frame] * (-1/[max speed]x + 1)

		self.canvas.update()

		if len(self.alive_players) == 0:
			self.finish()

		self.alive_players[0].neural_network.visualise()

		if render_graph:
			if self.distance == 0:
				plt.clf()
			conv = {0: "black", 1: "purple", 2: "blue", 3: "brown"}
			conv2 = {0: "jump", 1: "nothing", 2: "duck", 3: "drop"}
			[plt.scatter([self.distance], [node], c=conv[ind], label=conv2[ind], alpha=0.8*(ind==np.argmax(self.alive_players[0].node_layers[-1][0]))+0.2) for ind, node in enumerate(self.alive_players[0].node_layers[-1][0])]
			if self.distance == 0:
				legend = plt.legend(loc='upper left')
				for lh in legend.legendHandles: lh.set_alpha(1)

		self.distance += 1


	def finish(self):
		"""End of round"""
		self.scroll_speed = 6
		self.obstacles = np.array([[-1, 200, -1, 200, -1]])
		self.distance = 0
		self.alive_players = self.dead_players[:, 0]
		self.dead_players = np.empty((0,2))

		for player in self.alive_players:
			player.rendering = False

		self.recreate()


	def load_model(self):
		save_file = os.path.join(self.save_folder, self.save_name + '.npy')

		if os.path.isfile(save_file):
			return list(np.load(save_file, allow_pickle=True))
		else:
			print("no model loaded, path is empty")
			return False


# neural network class
class neural_network:
	"""Parent class for neural network based operations."""
	def __init__(self, game, nodes = [7, 250, 250, 4], activation_functions = [2, 2, 0], neural_network_type = 1):
		# assign variables
		self.game = game
		self.nodes = nodes
		self.rendering = False

		# use activation function matching the argument given
		self.activation_functions = []

		for activation_function in activation_functions:
			match activation_function:
				case 0 | "no activation function":
					self.activation_functions.append(lambda input: input)
					self.node_limit = [-np.inf, np.inf]
				case 1 | "relu":
					self.activation_functions.append(self.relu)
					self.node_limit = [0, np.inf]

				case 2 | "lrelu":
					self.activation_functions.append(self.lrelu)
					self.node_limit = [-np.inf, np.inf]

				case 3 | "softplus":
					self.activation_functions.append(self.softplus)
					self.node_limit = [0, np.inf]

				case 4 | "sigmoid":
					self.activation_functions.append(self.sigmoid)
					self.node_limit = [0, 1]

				case 5 | "tanh":
					self.activation_functions.append(self.tanh)
					self.node_limit = [-1, 1]

				case 6 | "swish":
					self.activation_functions.append(self.swish)
					self.node_limit = [-0.28, np.inf]

				case 7 | "mish":
					self.activation_functions.append(self.mish)
					self.node_limit = [-0.14, np.inf]

				case 8 | "RBF":
					self.activation_functions.append(self.RBF)
					self.node_limit = [0, 1]

				case 9 | "RBFx":
					self.activation_functions.append(self.RBFx)
					self.node_limit = [-0.43, 0.43]

				case 10 | "ELU":
					self.activation_functions.append(self.ELU)
					self.node_limit = [-1, np.inf]

				case _:
					raise NotImplementedError(f"Invalid activation function: {activation_function}")

		# setup and set functions up for the neural network type specified in the arguments
		match neural_network_type:
			case 1 | "FNN":
				self.node_function = self.FNN_node_function
				self.FNN_setup()

				"""
			case 2 | "RNN":
				self.node_function = self.RNN_node_function
				self.RNN_setup()

			case 3 | "LSTM":
				self.node_function = self.LSTM_node_function
				self.LSTM_setup()

			case 4 | "GRU":
				self.node_function = self.GRU_node_function
				self.GRU_setup()
				"""

			case _:
				raise NotImplementedError(f"Invalid neural network type: {neural_network_type}")


	def forward_propogate(self, inputs):
		if len(inputs) != self.nodes[0]: raise ValueError(f"Incorrect amount of inputs. Length of inputs should correspond to the first layer's node count/self.nodes[0] (currently {len(inputs)} inputs and {self.nodes[0]} nodes)")

		self.node_layers[0][0,1:] = inputs

		return self.node_function()


	def instance_normalization(self, inputs):
		bias = inputs[:, [0]]
		inputs = inputs[:, 1::]

		mean = np.average(inputs)
		variance = np.average((inputs-mean)**2)
		epsilon = 0.0000001

		return np.append(bias, (inputs-mean)/np.sqrt(np.average(variance)+epsilon), axis = 1)


	def relu(self, input):
		return np.maximum(input, 0)


	def lrelu(self, input):
		return np.maximum(input, 0.1 * input)


	def softplus(self, input):
		return np.log(1 + np.exp(input))


	def sigmoid(self, input):
		return 1/(1 + np.exp(-input))


	def tanh(self, input):
		return 2/(1 + np.exp(-input)) - 1


	def swish(self, input):
		return input/(1 + np.exp(-input))


	def mish(self, input):
		return input * np.tanh(np.log(1 + np.exp(input)))


	def RBF(self, input):
		return np.exp(-input**2)


	def RBFx(self, input):
		return np.exp(-input**2) * input


	def ELU(self, input):
		return np.piecewise(input, [input < 0, input >= 0], [lambda x: np.e**x - 1, lambda x: x])


	def layer_setup(self, inter_nodes = 1):
		self.node_layers = []
		for layer in range(len(self.nodes[:-1])):
			self.node_layers.append(np.empty((1, self.nodes[layer] + 1))) # empty node layer
			self.node_layers[-1][0, 0] = 1 # set the bias node to 1
		self.node_layers.append(np.empty((1, self.nodes[-1])))

		
		self.weight_layers = self.game.load_model()

		if self.weight_layers:
			return

		self.weight_layers = []

		for layer in range(len(self.nodes[:-1])):
			self.weight_layers.append(np.append(np.zeros((1, self.nodes[layer+1] * inter_nodes)), np.random.randn(self.nodes[layer], self.nodes[layer+1] * inter_nodes) * np.sqrt(2/(self.nodes[layer] * inter_nodes)), axis = 0)) # weight and bias layer. Initializes node weights to sqrt(2/last_layer_len) and bias to 0


	def FNN_setup(self):
		self.layer_setup()


	def FNN_node_function(self):
		for layer_index in range(len(self.node_layers[:-2])):
			if layer_index == 0:
				self.node_layers[layer_index+1][:,1:] = self.activation_functions[layer_index](self.node_layers[layer_index] @ self.weight_layers[layer_index])
			else:
				self.node_layers[layer_index+1][:,1:] = self.activation_functions[layer_index](self.instance_normalization(self.node_layers[layer_index]) @ self.weight_layers[layer_index])

		else:
			self.node_layers[-1] = self.activation_functions[-1](self.instance_normalization(self.node_layers[-2]) @ self.weight_layers[-1])

		return self.node_layers[-1]

	"""
	def RNN_setup(self):
		self.layer_setup()

		self.hidden_node = []
		self.wh = []

		for layer in range(len(self.nodes[:-1])):
			self.hidden_node.append(np.zeros((1, self.nodes[layer+1])))
			self.wh.append(np.random.randn(1, self.nodes[layer+1]))


	def RNN_node_function(self):
		for layer_index in range(len(self.node_layers[:-2])):
			layer_in = self.instance_normalization(self.node_layers[layer_index]) @ self.weight_layers[layer_index] + self.hidden_node[layer_index] * self.wh[layer_index]
			self.node_layers[layer_index+1][:,1:] = self.activation_functions[layer_index](layer_in)
			self.hidden_node[layer_index] = self.node_layers[layer_index+1][:,1:]

		else:
			layer_in = self.instance_normalization(self.node_layers[-2]) @ self.weight_layers[-1] + self.hidden_node[-1] * self.wh[-1]
			self.node_layers[-1] = self.activation_functions[-1](layer_in) # same as above, but the last node layer shape is slightly diff so we need diff slicing
			self.hidden_node[-1] = self.node_layers[-1]

		return self.node_layers[-1]


	def LSTM_setup(self):
		self.layer_setup(inter_nodes=4)

		self.hidden_node = []
		self.wh = []

		self.c = []
		self.wc = []

		for layer in range(len(self.nodes[:-1])):
			self.hidden_node.append(np.zeros((1, self.nodes[layer+1])))
			self.wh.append(np.random.randn(1, self.nodes[layer+1]*4))

			self.c.append(np.zeros((1, self.nodes[layer+1])))
			self.wc.append(np.random.randn(1, self.nodes[layer+1]*2))


	def LSTM_node_function(self):
		for layer_index in range(len(self.node_layers[:-2])):
			layer_in = self.instance_normalization(self.node_layers[layer_index]) @ self.weight_layers[layer_index] + np.repeat(self.hidden_node[layer_index],4) * self.wh[layer_index]

			a = self.sigmoid(layer_in[:, ::4] + self.c[layer_index]*self.wc[layer_index][::2])
			b = self.sigmoid(layer_in[:, 1::4] + self.c[layer_index]*self.wc[layer_index][1::2])
			c = self.tanh(layer_in[:, 2::4])
			d = self.sigmoid(layer_in[:, 3::4])

			self.c[layer_index] = self.c[layer_index]*a + b*c

			self.hidden_node[layer_index] = d * self.tanh(self.c[layer_index])

			self.node_layers[layer_index+1][:,1:] = self.hidden_node[layer_index]
		else:
			layer_in = self.instance_normalization(self.node_layers[-2]) @ self.weight_layers[-1] + np.repeat(self.hidden_node[-1],4) * self.wh[-1]

			a = self.sigmoid(layer_in[:, ::4] + self.c[-1]*self.wc[-1][::2])
			b = self.sigmoid(layer_in[:, 1::4] + self.c[-1]*self.wc[-1][1::2])
			c = self.tanh(layer_in[:, 2::4])
			d = self.sigmoid(layer_in[:, 3::4])

			self.c[-1] = self.c[-1]*a + b*c

			self.hidden_node[-1] = d * self.tanh(self.c[-1])

			self.node_layers[-1] = self.hidden_node[-1]

		return self.node_layers[-1]


	def GRU_setup(self):
		self.layer_setup(inter_nodes=3)

		self.hidden_node = []
		self.wh = []

		for layer in range(len(self.nodes[:-1])):
			self.hidden_node.append(np.zeros((1, self.nodes[layer+1])))
			self.wh.append(np.random.randn(1, self.nodes[layer+1]*3))


	def GRU_node_function(self):
		for layer_index in range(len(self.node_layers[:-2])):
			slice_max = int(2/3*self.weight_layers[layer_index].shape[1])

			layer_in = self.instance_normalization(self.node_layers[layer_index]) @ self.weight_layers[layer_index][:, :slice_max] + np.repeat(self.hidden_node[layer_index],2) * self.wh[layer_index][:, :slice_max]

			a = self.sigmoid(layer_in[:, ::2])
			b = self.sigmoid(layer_in[:, 1::2])

			c = self.tanh(self.node_layers[layer_index] @ self.weight_layers[layer_index][:, slice_max:] + a * self.hidden_node[layer_index] * self.wh[layer_index][:, slice_max:])

			self.hidden_node[layer_index] = (1-b)*self.hidden_node[layer_index] + b*c

			self.node_layers[layer_index+1][:,1:] = self.hidden_node[layer_index]
		else:
			slice_max = int(2/3*self.weight_layers[-1].shape[1])

			layer_in = self.instance_normalization(self.node_layers[-2]) @ self.weight_layers[-1][:, :slice_max] + np.repeat(self.hidden_node[-1],2) * self.wh[-1][:, :slice_max]

			a = self.sigmoid(layer_in[:, ::2])
			b = self.sigmoid(layer_in[:, 1::2])

			c = self.tanh(self.node_layers[-2] @ self.weight_layers[-1][:, slice_max:] + a * self.hidden_node[-1] * self.wh[-1][:, slice_max:])

			self.hidden_node[-1] = (1-b)*self.hidden_node[-1] + b*c

			self.node_layers[-1] = self.hidden_node[-1]

		return self.node_layers[-1]
	"""


	def visualise(self):
		if not render: return

		if not self.rendering:
			self.game.canvas.delete("nn visualisation")

			max_displayed_nodes = 6

			most_nodes = np.minimum(np.amax(self.nodes)+1*(np.argmax(self.nodes)<len(self.nodes)-1), max_displayed_nodes)

			circle_diameter = 20
			spacing_l = 50
			spacing_s = 10

			bbx1, bby1, bbx2, bby2 = [self.game.canvas_width - (len(self.nodes) * circle_diameter + (len(self.nodes) - 1) * spacing_l + spacing_s), spacing_s, self.game.canvas_width - spacing_s, circle_diameter * most_nodes + spacing_s * most_nodes] #x1, y1 is top left corner #bounding box

			self.game.canvas.create_rectangle((bbx1 - spacing_s, bby1 - spacing_s), (bbx2 + spacing_s + 10, bby2 + spacing_s), fill = "white", outline = "black", tag = "nn visualisation")

			self.visualised_nodes = np.array([[self.game.canvas.create_rectangle((bbx1 - spacing_s, bby1 - spacing_s), (bbx2 + spacing_s, bby2 + spacing_s), fill = "white", outline = "black"), -1, -1]]) #columns: tkinter object, node's level, node's position in level
			self.visualised_weights = np.array([[-1, -1, -1, -1]]) #tkinter object, first's level, first node, second node

			for _level in range(len(self.nodes)):
				for _node in range(np.minimum(self.nodes[_level]+1*(_level<len(self.nodes)-1), max_displayed_nodes)):
					self.visualised_nodes = np.append(self.visualised_nodes, [[self.game.canvas.create_oval(bbx1 + _level * (spacing_l + circle_diameter), (bby2 - bby1)/2 + bby1 - np.minimum(self.nodes[_level]+1*(_level<len(self.nodes)-1), max_displayed_nodes)/2 * circle_diameter - (np.minimum(self.nodes[_level]+1*(_level<len(self.nodes)-1), max_displayed_nodes) - 1)/2 * spacing_s + _node * (spacing_s + circle_diameter), bbx1 + circle_diameter + _level * (spacing_l + circle_diameter), (bby2 - bby1)/2 + bby1 - np.minimum(self.nodes[_level]+1*(_level<len(self.nodes)-1), max_displayed_nodes)/2 * circle_diameter - (np.minimum(self.nodes[_level]+1*(_level<len(self.nodes)-1), max_displayed_nodes) - 1)/2 * spacing_s + circle_diameter + _node * (spacing_s + circle_diameter), tag = "nn visualisation"), _level, _node]], axis = 0)
					if _level < len(self.nodes) - 1:
						for _node2 in range(1*(_level<len(self.nodes)-2), np.minimum(self.nodes[_level+1]+1*(_level<len(self.nodes)-2), max_displayed_nodes)):
							self.visualised_weights = np.append(self.visualised_weights, [[self.game.canvas.create_line(bbx1 + circle_diameter + _level * (spacing_l + circle_diameter), (bby2 - bby1)/2 + bby1 - ((np.minimum(self.nodes[_level]+1*(_level<len(self.nodes)-1), max_displayed_nodes) - 1) * spacing_s + (np.minimum(self.nodes[_level]+1*(_level<len(self.nodes)-1), max_displayed_nodes) - 2) * circle_diameter + circle_diameter)/2 + (circle_diameter + spacing_s) * _node, bbx1 + (_level + 1) * (spacing_l + circle_diameter), (bby2 - bby1)/2 + bby1 - ((np.minimum(self.nodes[_level + 1]+1*(_level+1<len(self.nodes)-1), max_displayed_nodes) - 1) * spacing_s + (np.minimum(self.nodes[_level + 1]+1*(_level+1<len(self.nodes)-1), max_displayed_nodes) - 2) * circle_diameter + circle_diameter)/2 + (circle_diameter + spacing_s) * _node2, tag = "nn visualisation"), _level, _node, _node2-1]], axis = 0)

				if self.nodes[_level] > max_displayed_nodes:
					center = [bbx1 + _level * (spacing_l + circle_diameter) + circle_diameter/2, (bby1 + bby2) / 2]
					dimensions = [1, 1]
					gap = 5

					self.game.canvas.create_oval(center[0] - dimensions[0]/2 - gap, center[1] - dimensions[1]/2, center[0] + dimensions[0]/2 - gap, center[1] + dimensions[1]/2, fill = "black", tag = "nn visualisation")
					self.game.canvas.create_oval(center[0] - dimensions[0]/2, center[1] - dimensions[1]/2, center[0] + dimensions[0]/2, center[1] + dimensions[1]/2, fill = "black", tag = "nn visualisation")
					self.game.canvas.create_oval(center[0] - dimensions[0]/2 + gap, center[1] - dimensions[1]/2, center[0] + dimensions[0]/2 + gap, center[1] + dimensions[1]/2, fill = "black", tag = "nn visualisation")

			self.rendering = True

		try:
			for _node in self.visualised_nodes[1::]:
				if _node[1] == len(self.nodes)-1 or _node[1] == 0:
					activation = self.node_layers[_node[1]] # - np.min(self.node_layers[_node[1]])
				else:
					activation = self.instance_normalization(self.node_layers[_node[1]])

				if np.amax(np.absolute(self.node_limit)) != np.inf:
					lim = np.amax(np.absolute(self.node_limit))
				else:
					lim = np.nanmax(np.absolute(activation))

				activation = activation[:, _node[2]][0] / (lim+0.000001*(lim == 0))

				converter_hex = {0:"0", 1:"1", 2:"2", 3:"3", 4:"4", 5:"5", 6:"6", 7:"7", 8:"8", 9:"9", 10:"A", 11:"B", 12:"C", 13:"D", 14:"E", 15:"F"}

				green = converter_hex[np.floor(15 * np.minimum(1, 1 + activation))] + converter_hex[np.floor((16 * np.minimum(1, 1 + activation) % 1) * 16)]
				red = converter_hex[np.floor(15 * np.minimum(1, 1 - activation))] + converter_hex[np.floor((16 * np.minimum(1, 1 - activation) % 1) * 16)]
				blue = converter_hex[np.floor(15 * np.minimum(1 + activation, 1 - activation))] + converter_hex[np.floor((16 * np.minimum(1 + activation, 1 - activation) % 1) * 16)]
				self.game.canvas.itemconfig(_node[0], fill="#" + red + green + blue)
			for _line in self.visualised_weights[1::]:
				array = self.weight_layers[_line[1]]
				lim = np.nanmax(np.absolute(array))
				scaled_array = array/(lim+0.000001)

				activation = scaled_array[_line[2], _line[3]]

				converter_hex = {0:"0", 1:"1", 2:"2", 3:"3", 4:"4", 5:"5", 6:"6", 7:"7", 8:"8", 9:"9", 10:"A", 11:"B", 12:"C", 13:"D", 14:"E", 15:"F"}

				red = converter_hex[np.floor(15 * np.minimum(1, 1 - activation))] + converter_hex[np.floor((16 * np.minimum(1, 1 - activation) % 1) * 16)]
				green = converter_hex[np.floor(15 * np.minimum(1, 1 + activation))] + converter_hex[np.floor((16 * np.minimum(1, 1 + activation) % 1) * 16)]
				blue = converter_hex[np.floor(15 * np.minimum(1 - activation, 1 + activation))] + converter_hex[np.floor((16 * np.minimum(1 - activation, 1 + activation) % 1) * 16)]

				self.game.canvas.itemconfig(_line[0], fill="#" + red + green + blue)
		except Exception as e:
			print(e)
			return

# player class
class player_class(neural_network):
	"""Contains a player's neural network, controls and other functions."""
	def __init__(self, game, death_score = -5, live_score = 1):
		self.neural_network = super()
		self.neural_network.__init__(game)

		self.game = game

		self.x = np.random.random() * 100 + 50 #random value between 50 and 150

		self.y = self.game.ground_y_value
		self.vy = 0

		self.jump_vy = 15
		self.drop_vy = -15

		self.w = 30
		self.h = 50

		self.state = 0 # {0: standing, 1: ducking, 2: airborn}
		self.gravity = 1

		self.tkobj = None # tk object to display player

		self.death_score = death_score
		self.live_score = live_score


	def render(self):
		"""The players start off invisible to increase framerate and because they do not need to be rendered in the subprocesses."""
		x1, y1, x2, y2 = self.x, self.y, self.x + self.w, self.y - self.h

		self.tkobj = self.game.canvas.create_rectangle((x1, y1), (x2, y2), fill="purple", outline="", tag = "player")


	def unrender(self):
		if self.tkobj:
			self.game.canvas.delete(self.tkobj)
			self.tkobj = None


	def jump(self):
		if self.state == 0:
			self.vy = self.jump_vy
			self.state = 2


	def drop(self):
		if self.state == 2:
			self.vy = self.drop_vy


	def duck(self):
		if self.state == 0:
			self.h = 30

			if self.tkobj:
				self.game.canvas.coords(self.tkobj, self.x, self.y, self.x + self.w, self.y - self.h)

			self.state = 1


	def stand(self):
		if self.state == 1:
			self.h = 50

			if self.tkobj:
				self.game.canvas.coords(self.tkobj, self.x, self.y, self.x + self.w, self.y - self.h)

			self.state = 0


	def detect_collision(self):
		obstacle_x1, obstacle_y1, obstacle_x2, obstacle_y2 = self.game.obstacles[0, 1:5].T

		if self.x+self.w > obstacle_x1 and self.x < obstacle_x2+self.game.scroll_speed and self.y-self.h < obstacle_y1 and self.y > obstacle_y2:
			self.die()


	def die(self):
		self.game.alive_players = self.game.alive_players[self.game.alive_players != self]
		self.game.dead_players = np.append(self.game.dead_players, [[self, self.game.distance]], axis = 0)

		self.unrender()


	def decide(self, state):
		decision = np.argmax(self.neural_network.forward_propogate(state))

		match decision:
			case 0:
				self.stand()
				self.jump()
			case 1:
				self.stand()
			case 2:
				self.duck()
			case 3:
				self.drop()
			case _:
				raise NotImplementedError("Mismatch between number of neural network outputs and actions")

		return decision


	def update_motion(self):
		next_obstacle = self.game.obstacles[self.game.obstacles[:, 3] > self.x][0]
		self.decide([(self.game.ground_y_value-self.y)/120, (self.vy)/15, (self.game.scroll_speed)/50, (next_obstacle[1]-self.x)/250, (next_obstacle[3]-self.x)/300, (self.game.ground_y_value-next_obstacle[2])/125, (self.game.ground_y_value-next_obstacle[4])/155])

		if self.game.ground_y_value - self.y < -1 * self.vy:
			dy = self.game.ground_y_value - self.y
			if self.state == 2: self.state = 0
		else:
			dy = -1 * self.vy

		if self.tkobj:
			self.game.canvas.move(self.tkobj, 0, dy)

		self.y += dy

		self.detect_collision()

		if self.state == 2:
			self.vy -= 1
		else:
			self.vy = 0


def toggle_render(event): 
	global render
	
	if render:
		render = False
	else:
		[player.render() for player in game.alive_players]
		[game.render_obstacles()]
		render = True


def toggle_render_graph(event): 
	global render_graph
	
	if render_graph:
		render_graph = False
		plt.clf()
	else:
		render_graph = True


render = False
render_graph = False

game = screen()

game.create()

game.root.bind("<space>", toggle_render)
game.root.bind("<BackSpace>", toggle_render_graph)

while True:
	game.update()





