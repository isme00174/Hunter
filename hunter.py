from astar_base import *
from ps_draw_h import *
import random

MAX_X, MAX_Y = 60, 45  # 场地的大小，默认60， 45 #2=30， 24
MAX_BLOCKS = 140  # 随机障碍物的数量，默认150 #2=80
GoalSight = 5  # 目标的视野，在视野外不会逃跑 - 这个数值不能太大，否则会提前把自己逼近死角，默认5
# 0-100的质数列表，供选择 2、3、5、7、11、13、17、19、23、29、31、37、41、43、47、53、59、61、67、71、73、79、83、89、97
SlowFactorList = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97)
HunterSlowFactor_ptr = 4
HunterSlowFactor = SlowFactorList[HunterSlowFactor_ptr]  # 猎人要比目标跑得慢，默认29 # 慢慢走67 # 快速走11
GoalSlowFactor_ptr = 0
GoalSlowFactor = SlowFactorList[GoalSlowFactor_ptr] # 两个速度不要是倍数关系，否则容易死循环，安全起见取质数，默认17# 慢慢走29 # 快速走3
RandomTurnRate = 0.1  # 随机转弯的概率 # 蚂蚁的程序里面是0.03，这里改成0.1，因为地图小
InitTurnRate = RandomTurnRate  # 记住一开始的随机转弯概率，逃跑的时候会临时改成更小的概率
EscapeSuccess = False  # 记录逃跑是否成功
HunterNum = 3  # 没有用
pause = False  # 暂停，手动控制
BeanEmpty = False  # 豆豆是否吃完
BeanCounter = 0  # 豆豆吃光后，每隔一定的时间自动生成一个新的
BeanCreatTime = 2 * fps  # 多少秒生成一个豆豆
MaxBeanCreat = 20  # 生成20个豆豆后停止，吃光后再重新生成
# 物体3个位置的数组定义，上一个位置，当前位置，下一个位置
POS = {"prev": 0,
       "now": 1,
       "next": 2}
STATE = {"随机走": 0,  # 目标的状态
         "吃豆豆": 3,
         "逃跑": 1,
         "离开死角": 2}
DIRS = {"上": (0, -1),
        "下": (0, 1),
        "左": (-1, 0),
        "右": (1, 0)}


# 猎人和猎物共有的特性
class Object:
    def __init__(self, id: GridLocation):
        self.pos = [id, id, id]  # 上一个位置，当前位置，下一个位置  # 目前next好像没什么用，是AI程序直接返回的，不需要赋值给这个变量
        self.path: list[Location] = []  # 寻路的路径，根据用途不同可以是追赶、逃跑、吃豆豆等的路径
        self.dir_x, self.dir_y = 0, 0  # 也许这个是不需要的，直接从pos prev 和 now 可以算出来
        self.slow_factor = 50  # 几个时钟周期才走一次，数值越大越慢，所以叫slow，不叫speed
        self.slow_counter = 0

    def random_next(self, nnn: list) -> GridLocation:  # 从nnn里面随机选择一个方向返回
        return nnn[random.randint(0, len(nnn)-1)]

    def exec_go(self, pos_next):  # 移动到参数指定的格子上去，并自动更新方向
        (x, y) = self.pos[POS["now"]]
        (x2, y2) = pos_next
        self.dir_x, self.dir_y = x2-x, y2-y
        # 这里要画图，清除上一个格子显示的物体
        self.pos[POS["prev"]] = self.pos[POS["now"]]
        self.pos[POS["now"]] = pos_next
        # 这里要画图，把物体显示在下一个格子

    def exec_go_dir(self, graph):  # 根据当前方向，向前走一步
        (x, y) = self.pos[POS["now"]]
        x2, y2 = x + self.dir_x, y + self.dir_y
        pos_next = (x2, y2)
        if graph.can_go(pos_next): self.exec_go(pos_next)

    def random_go1(self, graph: WeightedGraph):  # 这个程序能跑通，但是有点复杂，重新写一个简单点的
        (x, y) = pos_now = self.pos[POS["now"]]
        neib = list(graph.neighbors(pos_now))  # 返回的是一个filter，要用list()来定义一下
        if not neib: return self.pos[POS["prev"]]
        else:
            if self.dir_x == 0 and self.dir_y == 0: return self.random_next(neib)  # 刚开始没有方向，先定一个
            neib.remove(self.pos[POS["prev"]])
            if not neib: return self.pos[POS["prev"]]
            next_temp = (x+self.dir_x, y+self.dir_y)
            neib_len = len(neib)

            if neib_len >= 3:
                if random.random() > RandomTurnRate: return next_temp
                else:
                    neib.remove(next_temp)
                    return self.random_next(neib)
            elif neib_len == 2:
                if next_temp in neib:
                    if random.random() > RandomTurnRate: return next_temp
                    else:
                        neib.remove(next_temp)
                        return neib[0]
                else: return self.random_next(neib)
            elif neib_len == 1:
                return neib[0]
        # 已经决定了下一步走哪里，下面正式走

    def random_go(self, graph: WeightedGraph):  # 随机走
        (x, y) = pos_now = self.pos[POS["now"]]
        neib = list(graph.neighbors(pos_now))  # 返回的是一个filter，要用list()来定义一下
        if self.dir_x == 0 and self.dir_y == 0: return self.random_next(neib)  # 刚开始没有方向，先定一个
        neib.remove(self.pos[POS["prev"]])
        if not neib: return self.pos[POS["prev"]]  # 如果没路走了，返回回头的位置
        next_temp = (x + self.dir_x, y + self.dir_y)  # 按照直行的方向尝试往前走一步
        # 如果前方是可行的，而且不拐弯（仅小概率才拐弯)，直接往前走
        if random.random() > RandomTurnRate and next_temp in neib: return next_temp
        return self.random_next(neib)  # 小概率随机走

    def count_to_go(self) -> bool:  # 计数，到了时间周期才走一步，用于控制物体的速度
        self.slow_counter += 1
        if self.slow_counter >= self.slow_factor:
            self.slow_counter = 0
            return True
        return False


class Hunter(Object):
    def __init__(self, id: GridLocation):
        Object.__init__(self, id)
        self.slow_factor = HunterSlowFactor  # 两个速度不要是倍数关系，否则容易死循环
        self.catch_counter = 0  # 记录抓住目标的次数

    # 猎人移动的AI程序，参数end=目标的位置，要走向它
    def move(self, graph, disp, end):
        global EscapeSuccess
        if self.count_to_go():  # 到了走的时间，这里用计数器来控制速度
            clear_object(disp, self.pos[POS["now"]])  # 画图，先清除当前格子的显示
            # 如果有豆豆，重新画豆豆，因为猎人不会吃豆豆
            if self.pos[POS["now"]] in graph.beans: draw_bean(disp, self.pos[POS["now"]])
            # 调用A*寻路算法，找到到目标的路径
            self.path = reconstruct_path(a_star_search(graph, self.pos[POS["now"]], end),
                                                 self.pos[POS["now"]], end)
            if not self.path:  # 找不到路径
                # 第一种可能性是猎人和目标不连通
                if heuristic(self.pos[POS["now"]], end) > GoalSight: print("找不到到目标的路，请重启程序！")
                else:  # 第二种可能是位置跟目标重合，抓到了目标
                    EscapeSuccess = False  # 记录逃跑失败
                    self.catch_counter += 1
                    print("## 抓到了%d" % self.catch_counter + "次！")
                self.exec_go(self.random_go(graph))  # 不管哪种情况，都是随机走
            else:  # 为了避免死循环，每走23步，随便走一步
                if random.randint(0, 23) > 1: self.exec_go(self.path[0])  # 正常情况下，按照寻路的路径走一步
                else: self.exec_go(self.random_go(graph))  # 小概率随机走一步
            draw_hunter(disp, self.pos[POS["now"]])  # 画图，在新的位置上显示猎人


class Goal(Object):
    def __init__(self, id: GridLocation):
        Object.__init__(self, id)
        self.slow_factor = GoalSlowFactor  # 两个速度不要是倍数关系，否则容易死循环
        self.state = 0  # 目标AI移动的状态机
        self.success_counter = 0  # 记录成功逃跑的次数

    # 目标移动的主程序，输入start=猎人的位置，要避开它
    def move(self, graph, disp, start):
        if self.count_to_go():  # 到了走的时间，这里用计数器来控制速度
            clear_object(disp, self.pos[POS["now"]])  # 画图，先清除当前格子的显示
            if self.pos[POS["now"]] in graph.beans:  # 移动到有豆豆的位置
                graph.beans.remove(self.pos[POS["now"]])  # 吃掉豆豆
                pygame.display.set_caption("猎人追逐猎物-" + str(len(graph.beans)))  # 显示剩余的豆豆数量
            if pause: self.exec_go_dir(graph) # 暂停状态，不自动走，根据手动控制的方向走
            else: self.exec_go(self.move_state(graph, start))  # 根据AI算法走
            draw_goal(disp, self.pos[POS["now"]], self.state)  # 画图，在新的位置画目标

    # 远离猎人，输入猎人的位置，输出远离猎人可以走的新位置，如果到了死角，返回None
    def run_away(self, graph, start):
        my_heur = heuristic(start, self.pos[POS["now"]])  # 先计算自己距离猎人的距离
        for nei in graph.neighbors(self.pos[POS["now"]]):  # 遍历邻居格子中可以走的几个方向
            if heuristic(start, nei) > my_heur: return nei  # 返回远离猎人的格子的位置
        return None  # 没有找到远离猎人的格子，返回None

    # 把找豆豆和找逃跑点的两个函数合并成一个，用了Bito AI自动生成代码的功能，试一下能不能用 - 居然能用
    # 只输入一个参数时，是找豆豆；输入三个参数时，是找逃跑点，另外两个参数是：猎人的位置， 自己距离猎人的距离
    # 用BFS算法找到离自己最近的一个豆豆，返回路径和 豆豆或逃跑点 的位置
    def find_path(self, graph, start=None, my_heur=None):
        is_finding_escape = my_heur is not None  # 判断是不是在找逃跑点
        frontier = Queue()
        frontier.put(self.pos[POS["now"]])
        came_from: dict[Location, Optional[Location]] = {}  # 记录曾经去过的节点
        came_from[self.pos[POS["now"]]] = None

        while not frontier.empty():
            current: Location = frontier.get()
            if not is_finding_escape and current in graph.beans:  # early exit。 找到了一个豆豆
                break
            elif is_finding_escape and heuristic(start, current) > my_heur:  # early exit。 找到了相比自己当前的位置，与猎人的距离更远的一个点
                break
            for next in graph.neighbors(current):  # 在neighbors这个方法里面，已经把障碍物和超出边界的邻近节点过滤掉了
                if next not in came_from:  # 这里比较的是key
                    frontier.put(next)
                    came_from[next] = current
                    #
        return came_from, current

    # 用BFS算法找到离自己最近的一个豆豆，返回路径和豆豆的位置 —— 已经合并，不用
    # 都是BFS搜索，怎么跟下面的函数合并，只是判断条件不同，输入参数不同，用字典可以实现？
    def find_bean(self, graph):
        frontier = Queue()
        frontier.put(self.pos[POS["now"]])
        came_from: dict[Location, Optional[Location]] = {}  # 记录曾经去过的节点
        came_from[self.pos[POS["now"]]] = None

        while not frontier.empty():
            current: Location = frontier.get()
            if current in graph.beans:  # early exit。 找到了一个豆豆
                break
            for next in graph.neighbors(current):  # 在neighbors这个方法里面，已经把障碍物和超出边界的邻近节点过滤掉了
                if next not in came_from:  # 这里比较的是key
                    frontier.put(next)
                    came_from[next] = current
        #
        return came_from, current

    # 用BFS算法找到一个最近的逃跑点，就是相比自己当前的位置，与猎人的距离大一格的一个点，返回路径和逃跑点 —— 已经合并，不用
    # 输入：猎人的位置， 自己距离猎人的距离
    def find_escape(self, graph, start, my_heur):
        frontier = Queue()
        frontier.put(self.pos[POS["now"]])
        came_from: dict[Location, Optional[Location]] = {}  # 记录曾经去过的节点
        came_from[self.pos[POS["now"]]] = None

        while not frontier.empty():
            current: Location = frontier.get()
            if heuristic(start, current) > my_heur:  # early exit。 找到了相比自己当前的位置，与猎人的距离更远的一个点
                break
            for next in graph.neighbors(current):  # 在neighbors这个方法里面，已经把障碍物和超出边界的邻近节点过滤掉了
                if next not in came_from:  # 这里比较的是key
                    frontier.put(next)
                    came_from[next] = current
        #
        return came_from, current

    # 用BFS算法找到一个最近的逃跑点，就是相比自己当前的位置，与猎人的距离大一格的一个点，只返回逃跑点 #所以不用
    def find_escape1(self, graph, start, my_heur) -> GridLocation:
        frontier = Queue()
        frontier.put(self.pos[POS["now"]])
        came_from: dict[Location, Optional[Location]] = {}  # 记录曾经去过的节点
        came_from[self.pos[POS["now"]]] = None

        while not frontier.empty():
            current: Location = frontier.get()
            if heuristic(start, current) > my_heur:  # early exit。 找到了比自己当前的位置，与猎人的距离大一格的一个点
                return current
            for next in graph.neighbors(current):  # 在neighbors这个方法里面，已经把障碍物和超出边界的邻近节点过滤掉了
                if next not in came_from:  # 这里比较的是key
                    frontier.put(next)
                    came_from[next] = current
        # 如果没有找到，返回None
        return None

    # 目标移动的AI算法，输入猎人的位置
    # 这个逃离算法很高效，目标速度是猎人的速度2被以上，基本上能跑掉
    def move_state(self, graph, start):
        global EscapeSuccess, BeanEmpty
        my_heur = heuristic(start, self.pos[POS["now"]])
        if self.state == STATE["随机走"]:
            if my_heur > GoalSight:  # 猎人还没有进入视野
                if graph.beans:  # 还有剩余的豆豆
                    # 找到最近的一颗豆豆的路径和位置，这个函数在只有一个参数时是找豆豆
                    came_from, bean_to_go = self.find_path(graph)
                    self.path = reconstruct_path(came_from, self.pos[POS["now"]], bean_to_go)  # 路径不含终点
                    self.path.append(bean_to_go)  # 加上终点：豆豆的位置
                    self.state = STATE["吃豆豆"]
                else:  # 豆豆吃完了
                    if not BeanEmpty:  # 刚刚检测到吃完，状态还没有修改的时候，显示一次
                        print("豆豆吃完啦！ 开始随机走...")
                        BeanEmpty = True  # 把状态修改为吃完，下次就不会显示了
                    return self.random_go(graph)  # 如果没有豆豆了，随机走
            else:  # 猎人已经进入视野，赶快逃啊
                self.state = STATE["逃跑"]
        if self.state == STATE["吃豆豆"]:
            if my_heur > GoalSight:  # 猎人还没有进入视野
                if not self.path:  # 已经到达豆豆的位置
                    self.state = STATE["随机走"]
                else:  # 朝着豆豆的方向走一步
                    next = self.path[0]
                    self.path.remove(next)
                    return next
                return self.random_go(graph)  # 随机走兜底
            else:  # 猎人已经进入视野，赶快逃啊
                self.state = STATE["逃跑"]
        if self.state == STATE["逃跑"]:
            if my_heur > GoalSight:  # 猎人超出视野，恢复随机走状态
                self.state = STATE["随机走"]
            ggg = self.run_away(graph, start)  # 远离猎人的方向
            if not ggg:  # 走到死角，没法远离了
                # 寻找逃跑点的路径和位置，这个函数在有三个参数时是找逃跑点
                came_from, escape = self.find_path(graph, start, my_heur)
                print("逃跑目的地:", escape)
                EscapeSuccess = True  # 默认逃跑成功，除非中途被抓住
                self.path = reconstruct_path(came_from, self.pos[POS["now"]], escape)  # 路径不含终点
                self.path.append(escape)  # 加上终点：逃离点
                self.state = STATE["离开死角"]
            else:  # 远离猎人的方向可以走，就往这里走
                return ggg
        if self.state == STATE["离开死角"]:  # 沿着刚才找到的逃跑路线逃跑，中间不管猎物在哪里，直到到达逃跑点为止
            if not self.path:  # 路径走完了 = 到达逃跑的终点
                if EscapeSuccess:  # 中间没有被抓住过
                    self.success_counter += 1
                    print("-- 成功%d次！ --" % self.success_counter)
                self.state = STATE["随机走"]
            else:  # 继续沿着逃跑的路径走
                next = self.path[0]
                self.path.remove(next)
                return next
            return self.random_go(graph)  # 随机走兜底

    # 这个逃离算法很高效，目标速度是猎人的速度2被以上，基本上能跑掉
    # 找到逃跑点后，还要用A*寻路找一遍，有点浪费，直接用BFS输出的路径即可，所以不用
    def move_state2(self, graph, start):
        global EscapeSuccess
        my_heur = heuristic(start, self.pos[POS["now"]])
        if self.state == STATE["随机走"]:
            if my_heur > GoalSight:
                return self.random_go(graph)
            else:
                self.state = STATE["逃跑"]
        if self.state == STATE["逃跑"]:
            if my_heur > GoalSight:
                self.state = STATE["随机走"]
            ggg = self.run_away(graph, start)  # 远离猎人的方向
            if not ggg:  # 走到死角，没法远离了
                escape = self.find_escape(graph, start, my_heur)
                print("逃跑目的地:", escape)
                EscapeSuccess = True
                came_from = a_star_search(graph, self.pos[POS["now"]], escape)
                self.path = reconstruct_path(came_from, self.pos[POS["now"]], escape)  # 路径不含终点
                self.path.append(escape)  # 加上终点：逃离点
                self.state = STATE["离开死角"]
            else: return ggg
        if self.state == STATE["离开死角"]:
            if not self.path:
                if EscapeSuccess:
                    self.success_counter += 1
                    print("-- 成功%d次！ --" % self.success_counter)
                self.state = STATE["随机走"]
            else:
                next = self.path[0]
                self.path.remove(next)
                return next
            return self.random_go(graph)  # 随机走

    # 这个是进入死角后随机跑，避开猎人的走法，已经有比较高的效率。还是不够好，写一个更好的
    def move_state1(self, graph, start):
        global RandomTurnRate
        my_heur = heuristic(start, self.pos[POS["now"]])
        if self.state == STATE["随机走"]:
            if my_heur > GoalSight:
                return self.random_go(graph)
            else:
                self.state = STATE["逃跑"]
        if self.state == STATE["逃跑"]:
            if my_heur > GoalSight:
                self.state = STATE["随机走"]
                RandomTurnRate = InitTurnRate  # 恢复到原来的随机转弯概率
            ggg = self.run_away(graph, start)  # 远离猎人的方向
            if not ggg:  # 走到死角，没法远离了
                self.state = STATE["离开死角"]
                # RandomTurnRate *= 2  # 为了快速逃离现场，尽量不转弯，有多远走多远 - 好像效果也一般，容易一直在死角转悠
            else: return ggg
        if self.state == STATE["离开死角"]:
            if my_heur > GoalSight:
                self.state = STATE["随机走"]
                RandomTurnRate = InitTurnRate  # 恢复到原来的随机转弯概率
            if my_heur == 0:  # 跟猎人重叠，不要随机走，赶快跑啊
                self.state = STATE["逃跑"]
            return self.random_go(graph)  # 先随机走，后面再补充更聪明的算法


# 初始化豆豆，用BFS算法，从目标开始，把能连通的每个点加上豆豆
def initial_bean(graph, end):
    beans = []
    frontier = Queue()
    frontier.put(end)
    came_from: dict[Location, Optional[Location]] = {}  # 记录曾经去过的节点
    came_from[end] = None

    while not frontier.empty():
        current: Location = frontier.get()
        for next in graph.neighbors(current):  # 在neighbors这个方法里面，已经把障碍物和超出边界的邻近节点过滤掉了
            if next not in came_from:  # 这里比较的是key
                frontier.put(next)
                beans.append(next)  # 注意，这里应该放next而不是current
                came_from[next] = current
    return beans


# 初始化豆豆，没有墙，而且能跟目标连通的点都填满豆豆
# —— 这个版本要一个一个地判断跟目标是否连通，地图大了以后，速度巨慢，启动程序就跟死机了一样，改成用BFS算法一次性生成
def initial_bean1(graph, end):
    beans = []
    for y in range(0, graph.height):
        for x in range(0, graph.width):
            if (x, y) in graph.walls: continue  # 有墙的点跳过
            if end in a_star_search(graph, (x, y), end): beans.append((x, y))  # 能跟目标连通的点，加上豆豆
    return beans


# 新增一颗豆豆，输入目标的位置，输出新的豆豆的位置
def creat_bean(graph, end):
    while True:
        y = random.randint(0, graph.height-1)
        x = random.randint(0, graph.width-1)
        if (x, y) in graph.walls: continue  # 不能是墙
        if (x, y) in graph.beans: continue  # 不能跟已有的豆豆重复
        if end in a_star_search(graph, (x, y), end):  # 该格子与目标能够连通，可行
            return (x, y)
            break


# 初始化墙，输入场地的长和宽
def initial_wall(xxx, yyy):
    walls = []
    # 再加上一些障碍物
    MaxBlock = MAX_BLOCKS  # 障碍物的数目 - 150比较平均
    count = 0
    while count < MaxBlock:
        # 长方形的左上角坐标
        x1, y1 = random.randint(1, xxx - 1), random.randint(1, yyy - 1)
        #  长方形的宽和高，最大是场地的的1/10
        dx, dy = random.randint(1, int(xxx / 10)), random.randint(1, int(yyy / 10))
        if x1 + dx >= xxx or y1 + dy >= yyy : continue  # 不能超过边界
        # 用墙的点阵填充长方形  # 这个程序以前是直接用长方形表示墙的，新的程序是点阵，所以一个一个点去填充
        for y in range(y1, y1+dy):
            for x in range(x1, x1+dx):
                walls.append((x, y))
        count += 1
    # 4个边拦一道，避免贴边走
    y = int(yyy/2)
    for x in range(0, 5): walls.append((x, y))
    for x in range(xxx-5, xxx): walls.append((x, y))
    x = int(xxx / 2)
    for y in range(0, 4): walls.append((x, y))
    for y in range(yyy - 4, yyy): walls.append((x, y))
    return walls


# 初始化猎人的位置，输入场地的长和宽
def initial_start(www, xxx, yyy):
    while 1:
        x = random.randint(0, 4)
        y = random.randint(yyy-5, yyy-1)
        if (x, y) not in www:
            sss = (x, y)
            return sss


# 初始化目标的位置，输入场地的长和宽
def initial_end(www, xxx, yyy):
    while 1:
        x = random.randint(5, xxx-1)
        y = random.randint(0, yyy-6)
        if (x, y) not in www:
            sss = (x, y)
            return sss


# 测试基本环境的程序
def main1():
    xxx, yyy = MAX_X, MAX_Y
    diagram_random = GridWithWeights(xxx, yyy)
    diagram_random.walls = initial_wall(xxx, yyy)
    start = initial_start(diagram_random.walls, xxx, yyy)
    goal = initial_end(diagram_random.walls, xxx, yyy)
    came_from = a_star_search(diagram_random, start, goal)
    draw_grid_win(diagram_random, path=reconstruct_path(came_from, start=start, goal=goal), start=start, goal=goal)


def main():
    global pause, BeanCounter, BeanEmpty, GoalSlowFactor_ptr, HunterSlowFactor_ptr, GoalSlowFactor, HunterSlowFactor
    # 初始化环境
    xxx, yyy = MAX_X, MAX_Y
    diagram_random = GridWithWeights(xxx, yyy)
    diagram_random.walls = initial_wall(xxx, yyy)
    ''' # 因为用了相同的寻路算法，所以多个猎人的意义不大，最后都会重叠在一起，这里就当学习怎么初始化数组
    starts: list[GridLocation] = [initial_start(diagram_random.walls, xxx, yyy) for i in range(HunterNum)]
    # 初始化一个类的数组的例子： emm=[myClass() for i in range(3)]
    hunters = [Hunter(starts[i]) for i in range(HunterNum)]
    '''
    start = initial_start(diagram_random.walls, xxx, yyy)
    hunter = Hunter(start)
    end = initial_end(diagram_random.walls, xxx, yyy)
    goal = Goal(end)
    diagram_random.beans = initial_bean(diagram_random, end)

    # 界面初始化
    pygame.init()
    Main_Clock = pygame.time.Clock()
    Main_Display = pygame.display.set_mode((xxx * cell_size, yyy * cell_size))
    pygame.display.set_caption('猎人追逐猎物')
    Main_Display.fill(COLORS["bg"])
    # 下面是画图程序
    draw_lines(diagram_random, Main_Display)
    draw_walls(diagram_random, Main_Display)
    draw_beans(diagram_random, Main_Display)
    # 结束画图
    pygame.display.update()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # 接收到退出事件后退出程序
                close_win()
            elif event.type == KEYDOWN:  # KEYDOWN 按键被按下
                if event.key == K_ESCAPE:  # 退出程序
                    # print('你按下了Esc键，退出程序')
                    close_win()
                elif event.key == K_SPACE: pause = not pause  # 暂停，手动控制
                elif event.key == K_EQUALS:  # 目标加速
                    if GoalSlowFactor_ptr >= 1:
                        GoalSlowFactor_ptr -= 1
                        goal.slow_factor = GoalSlowFactor = SlowFactorList[GoalSlowFactor_ptr]
                elif event.key == K_MINUS:  # 目标减速
                    if GoalSlowFactor_ptr <= len(SlowFactorList) - 2 \
                            and GoalSlowFactor_ptr < HunterSlowFactor_ptr - 1:  # 目标速度不能低于猎人
                        GoalSlowFactor_ptr += 1
                        goal.slow_factor = GoalSlowFactor = SlowFactorList[GoalSlowFactor_ptr]
                elif event.key == K_RIGHTBRACKET:  # 猎人加速
                    if HunterSlowFactor_ptr >= 1 \
                            and HunterSlowFactor_ptr > GoalSlowFactor_ptr + 1:  # 猎人速度不能超过目标
                        HunterSlowFactor_ptr -= 1
                        hunter.slow_factor = HunterSlowFactor = SlowFactorList[HunterSlowFactor_ptr]
                elif event.key == K_LEFTBRACKET:  # 猎人减速
                    if HunterSlowFactor_ptr <= len(SlowFactorList) - 2:
                        HunterSlowFactor_ptr += 1
                        hunter.slow_factor = HunterSlowFactor = SlowFactorList[HunterSlowFactor_ptr]
                if pause and goal.state == STATE["随机走"]:  # 在暂停状态，可以手动控制移动，只在随机走状态才行
                    if event.key == K_UP: goal.dir_x, goal.dir_y = DIRS["上"]
                    elif event.key == K_DOWN: goal.dir_x, goal.dir_y = DIRS["下"]
                    elif event.key == K_LEFT: goal.dir_x, goal.dir_y = DIRS["左"]
                    elif event.key == K_RIGHT: goal.dir_x, goal.dir_y = DIRS["右"]
        # 下面是控制主程序
        if not pause or goal.state == STATE["随机走"]:  # 在随机走状态，即使暂停也继续走，因为可以手动控制
            goal.move(diagram_random, Main_Display, hunter.pos[POS["now"]])
        if not pause:
            hunter.move(diagram_random, Main_Display, goal.pos[POS["now"]])
            '''  # 吃豆豆的时候就不能显示逃跑路线了，跟吃豆豆路线区分不开
            if goal.path:  # 把逃跑的路线画出来
                for pp in goal.path:
                    draw_path_dot(Main_Display, pp) '''
        # 定期生成豆豆
        if BeanEmpty and len(diagram_random.beans) <= MaxBeanCreat:
            BeanCounter += 1
            if BeanCounter >= BeanCreatTime:
                id = creat_bean(diagram_random, goal.pos[POS["now"]])
                diagram_random.beans.append(id)
                draw_bean(Main_Display, id)
                print("生成一颗新的豆豆", id)
                pygame.display.set_caption("猎人追逐猎物-" + str(len(diagram_random.beans)))
                BeanCounter = 0
                if len(diagram_random.beans) >= MaxBeanCreat:
                    print("已经有%d颗豆豆了，吃完再说..." % len(diagram_random.beans))
                    BeanEmpty = False
        pygame.display.update()
        Main_Clock.tick(fps)


if __name__ == '__main__':
    main()
