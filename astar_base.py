# Sample code from https://www.redblobgames.com/pathfinding/a-star/
# Copyright 2014 Red Blob Games <redblobgames@gmail.com>
#
# Feel free to use this code in your own projects, including commercial projects
# License: Apache v2.0 <http://www.apache.org/licenses/LICENSE-2.0.html>

from __future__ import annotations
# some of these types are deprecated: https://www.python.org/dev/peps/pep-0585/
from typing import Protocol, Iterator, Tuple, TypeVar, Optional
import collections, heapq

T = TypeVar('T')
Location = TypeVar('Location')
GridLocation = Tuple[int, int]


# 基础图的类
class Graph(Protocol):
    def neighbors(self, id: Location) -> list[Location]: pass


# 简单图的类
class SimpleGraph:
    def __init__(self):
        self.edges: dict[Location, list[Location]] = {}

    def neighbors(self, id:Location) -> list[Location]:
        return self.edges[id]


# 这个类实现了一个简单的先进先出堆栈功能。   me：Python现成的堆栈类可以调用，为什么还要自己重新写一个类？
class Queue:
    def __init__(self):
        self.elements = collections.deque()

    def empty(self) -> bool:
        return not self.elements  # 只要有内容，都返回False

    def put(self, x:T):
        self.elements.append(x)  # 压栈

    def get(self) -> T:
        return self.elements.popleft()  # 出栈，难道还有左右可选？ 左代表先进先出？


# 定义一个矩阵空间，宽度，高度，里面有一些障碍物
class SquareGrid:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.walls: list[GridLocation] = []
        self.beans: list[GridLocation] = []  # 增加豆豆，玩家的目标是吃掉豆豆

    # 判断某个位置是否在矩阵的范围内
    def in_bounds(self, id: GridLocation) -> bool:
        (x, y) = id
        return 0 <= x < self.width and 0 <= y < self.height

    # 判断是否是障碍物
    def passable(self, id: GridLocation) -> bool:
        return id not in self.walls

    # 返回可以往前走的邻近节点，上下左右4个方向，排除超出边界的节点，和障碍物
    def neighbors(self, id:GridLocation) -> Iterator[GridLocation]:
        (x, y) = id
        neighbors = [(x+1, y), (x-1, y), (x, y-1), (x, y+1)]  # E W N S， # 如果x-y加起来是单数，邻居的顺序是：右-左-上-下
        # see "Ugly paths" section for an explanation:
        if (x+y)%2 == 0: neighbors.reverse()  # S N W E  # 如果x-y加起来是双数，则改成：下-上-左-右
        results = filter(self.in_bounds, neighbors)
        results = filter(self.passable, results)
        return results
    # 以上是原寻路算法的内容，下面增加猎人的部分

    # 判断既不是墙，也不出界，可以走
    def can_go(self, id: GridLocation) -> bool:
        return self.passable(id) and self.in_bounds(id)


# 带有权重的图
class WeightedGraph(Graph):
    def cost(self, from_id: Location, to_id: Location) -> float: pass


# 带有权重的矩阵空间，继承了上面的矩阵空间。增加了地图的权重，例如马路的权重高，爬山的权重低。cost = 走这个路径的代价
# 为了简单起见，这里只取了目标节点，没有计算起点到终点的矢量来计算
class GridWithWeights(SquareGrid):
    def __init__(self, width: int, height: int):
        super().__init__(width, height)
        self.weights: dict[GridLocation, float] = {}

    # 没看懂这个函数怎么计算的？？
    def cost(self, from_node: GridLocation, to_node: GridLocation) -> float:
        return self.weights.get(to_node, 1)


# 带有优先级的队列，除了记录位置，还记录了从起点到这个位置所花费的代价
# 如果是均匀的地图，每距离一个格子代价+1，如果是带权重的地图，加上权重，例如这个例子，爬山是+5
# 核心！！！ 出栈的时候，自动会选择代价最小的那个节点弹出来，而不是先进先出
# 其实Python的默认库queue里面也有PriorityQueue类，为什么要另外创建一个？
class PriorityQueue:
    def __init__(self):
        self.elements: list[tuple[float, T]] = []

    def empty(self) -> bool:
        return not self.elements

    def put(self, item: T, priority: float):
        heapq.heappush(self.elements, (priority, item))

    def get(self) -> T:
        return heapq.heappop(self.elements)[1]
# 以上是基础类，下面是寻路实现的程序


# 这个函数只是简单x-y差值的相加，不是计算直线距离
def heuristic(a: GridLocation, b: GridLocation) -> float:
    (x1, y1) = a
    (x2, y2) = b
    return abs(x1 - x2) + abs(y1 - y2)


def a_star_search(graph: WeightedGraph, start: Location, goal: Location):
    frontier = PriorityQueue()
    frontier.put(start, 0)
    came_from: dict[Location, Optional[Location]] = {}
    cost_so_far: dict[Location, float] = {}
    came_from[start] = None
    cost_so_far[start] = 0

    while not frontier.empty():
        current: Location = frontier.get()

        if current == goal:
            break

        for next in graph.neighbors(current):
            new_cost = cost_so_far[current] + graph.cost(current, next)
            if next not in cost_so_far or new_cost < cost_so_far[next]:
                cost_so_far[next] = new_cost  # 原文是这样的，只记录了从起点到这个格子的代价，没有加上到终点的距离
                priority = new_cost + heuristic(next, goal)  # 整个寻路程序跟上面的dijkstra相比，只多这一句话
                frontier.put(next, priority)
                came_from[next] = current

    return came_from


# 从路径指向图的字典里面取出路径，是从结果倒着取的，因为指向图记录的是每一个节点的上一个节点，所以只能从终点回溯
def reconstruct_path(came_from: dict[Location, Location],
                     start: Location, goal: Location) -> list[Location]:

    current: Location = goal
    path: list[Location] = []
    if goal not in came_from: # no path was found
        return []
    while current != start:
        if current != goal: path.append(current)  # 我把它改成了不包含终点
        # path.append(current)  # 原程序是这一行，包含终点
        current = came_from[current]
    # path.append(start) # optional，包含起点，我会把它去掉
    path.reverse()  # optional，把路径改成从起点开始
    return path
