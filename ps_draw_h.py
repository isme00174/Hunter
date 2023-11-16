from astar_base import *
import pygame
from pygame.locals import *
import sys

fps = 100  # 帧率，默认100
cell_size = 20  # 格子的宽度，默认20， #2 = 40
hunter_size = 12  # 猎人的大小， 默认12， #2=20
goal_size = 12  # 目标的大小，默认12， #2=20
bean_size = 4  # 豆豆的大小，默认6

# 画图一些常数的定义
COLORS = {
    "bg": (200, 200, 200),  # 背景颜色
    "select": (0, 139, 139),
    "current": (255, 192, 203),
    "line": (175, 175, 175),
    "wall": (50, 50, 50),
    "start": (200, 200, 0),  # 原来是 65, 105, 225 RoyalBlue
    "end": (0, 192, 0),  # 原来是 0, 128, 0
    "goal": (255, 255, 0),  # 亮黄色
    "visited":(153, 50, 204),
    "current-text": (255,255,255),
    "visited-text": (255,255,255),
    "visit-line": (0, 255, 0),
    "cost-text": (255, 255, 255),
    "black": (0, 0, 0),
    "heuristic-text": (255, 255, 255),
    "priority-text": (255,255,0),
    "path": (0, 0, 255),  # 原来是 0, 0, 255
    "bean": (255, 255, 255)  # 64, 200, 100
}
COLORS["current"] = (135, 206, 250)
COLORS["visited"] = (100, 100, 125)
# COLORS["wall"] = (251, 114, 153) 原来是这样的深粉色
COLORS["wall"] = (64, 128, 128)


# utility functions for dealing with square grids
# id除以宽度取整，取余，分别作为x和y，形成一个位置[x, y]
def from_id_width(id, width):
    return (id % width, id // width)


# 画矩阵里面的一个节点
def draw_tile(graph, id, style):
    r = " . "
    if 'number' in style and id in style['number']: r = " %-2d" % style['number'][id]
    if 'point_to' in style and style['point_to'].get(id, None) is not None:
        (x1, y1) = id
        (x2, y2) = style['point_to'][id]
        if x2 == x1 + 1: r = " > "
        if x2 == x1 - 1: r = " < "
        if y2 == y1 + 1: r = " v "
        if y2 == y1 - 1: r = " ^ "
    if 'path' in style and id in style['path']:   r = " @ "
    if 'start' in style and id == style['start']: r = " A "
    if 'goal' in style and id == style['goal']:   r = " Z "
    if id in graph.walls: r = "###"
    return r


# 画整个矩阵
def draw_grid(graph, **style):  # 加了两个星号 ** 的参数会以字典的形式导入。这样就可以有多个参数
    print("___" * graph.width)
    for y in range(graph.height):
        for x in range(graph.width):
            # 画一个格子
            print("%s" % draw_tile(graph, (x, y), style), end="")
        print()
    print("~~~" * graph.width)


# 关闭游戏界面
def close_win():
    pygame.quit()
    sys.exit()


# 原程序里面的c = width, r = height
def draw_lines(graph, win):  # 绘制方格线
    for ci in range(graph.width):
        cx = cell_size * ci
        pygame.draw.line(win, COLORS["line"], (cx, 0), (cx, graph.height * cell_size))

    for ri in range(graph.height):
        ry = cell_size * ri
        pygame.draw.line(win, COLORS["line"], (0, ry), (graph.width * cell_size, ry))


# 画一个格子，如果是墙，充满格子（覆盖方格线），其他物体缩小一个像素，不覆盖方格线
def draw_cell(win, ci, ri, color):
    if color == "wall": rect = (ci * cell_size, ri * cell_size, cell_size, cell_size)
    else: rect = (ci * cell_size + 1, ri * cell_size + 1, cell_size - 2, cell_size - 2)
    pygame.draw.rect(win, COLORS[color], rect)


# 画矩阵里面的一个节点，number 和 point_to 不能同时选，否则会重叠
def draw_tile_win(graph, win, id, style):
    sc, sr = id
    if id in graph.walls: draw_cell(win, sc, sr, "wall")
    if 'start' in style and id == style['start']: draw_cell(win, sc, sr, "start")
    if 'goal' in style and id == style['goal']: draw_cell(win, sc, sr, "end")
    if 'path' in style and id in style['path']: draw_cell(win, sc, sr, "path")
    if 'number' in style and id in style['number']: draw_count(win, sc, sr, style['number'][id])
    if 'point_to' in style and style['point_to'].get(id, None) is not None:
        draw_vline(win, id, style['point_to'][id])


# 画矢量箭头，好消息是箭头的长度是自适应的，自动计算为从上一个格子的中间到下一个格子的中间，需要修改线条的粗细，默认是3
def draw_vline(win, v, prev_v):
    sx = prev_v[0] * cell_size + cell_size // 2
    sy = prev_v[1] * cell_size + cell_size // 2
    ex = v[0] * cell_size + cell_size // 2
    ey = v[1] * cell_size + cell_size // 2

    dx, dy = (ex - sx), (ey - sy)

    start_pos = (sx + dx // 4, sy + dy // 4)
    end_pos = (ex - dx // 4, ey - dy // 4)
    pygame.draw.line(win, COLORS["visit-line"], start_pos, end_pos, 3)  # 最后一个参数是线条的粗细，默认是3，方块默认大小44
    # 原下载的程序是这样的，不支持width=3这样传递参数 pygame.draw.line(self.win, COLORS["visit-line"], start_pos, end_pos, width=3)

    arrow_hw = 5  # 箭头的大小，默认是5，，方块默认大小44
    if dy == 0:
        x1 = ex - dx // 8
        x2 = ex - dx * 3 // 8
        arrow_points = [(x1, sy), (x2, sy - arrow_hw), (x2, sy + arrow_hw)]
        pygame.draw.polygon(win, COLORS["visit-line"], arrow_points)

    if dx == 0:
        y1 = ey - dy // 8
        y2 = ey - dy * 3 // 8
        arrow_points = [(sx, y1), (sx - arrow_hw, y2), (sx + arrow_hw, y2)]
        pygame.draw.polygon(win, COLORS["visit-line"], arrow_points)


# 画路径代价的数字
def draw_count(win, ci, ri, values):
    FONTS = pygame.font.Font(pygame.font.get_default_font(), 16)  # 默认字体大小是16， 格子默认大小是44
    tlst = FONTS.render("%s" % values, True, COLORS["cost-text"])
    top, left = ri * cell_size, ci * cell_size
    quarter = cell_size // 2
    cxy = (left + quarter, top + quarter)
    text_rect = tlst.get_rect(center=cxy)
    win.blit(tlst, text_rect)


def draw_grid_win(graph, **style):
    pygame.init()
    Main_Clock = pygame.time.Clock()
    Main_Display = pygame.display.set_mode((graph.width*cell_size, graph.height*cell_size))
    pygame.display.set_caption('A*寻路算法演示程序')
    Main_Display.fill(COLORS["bg"])
    # 下面是画图程序
    draw_lines(graph, Main_Display)
    for y in range(graph.height):
        for x in range(graph.width):
            # 画一个格子
            draw_tile_win(graph, Main_Display, (x, y), style)
    # 结束画图
    pygame.display.update()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # 接收到退出事件后退出程序
                close_win()
        if event.type == KEYDOWN:  # KEYDOWN 按键被按下
            if event.key == K_ESCAPE:
                # print('你按下了Esc键，退出程序')
                close_win()
        pygame.display.update()
        Main_Clock.tick(fps)
# 以上是直接从寻路算法拷贝过来的，下面是猎人程序新写的


# 单独画障碍物的程序
def draw_walls(graph, win):
    for id in graph.walls:
        sc, sr = id
        draw_cell(win, sc, sr, "wall")


def clear_object(win, id):  # 用背景颜色去清除一个格子
    sc, sr = id
    draw_cell(win, sc, sr, "bg")


def draw_hunter(win, id):  # 画猎人，一个圆圈
    sc, sr = id
    pygame.draw.circle(win, COLORS["path"], (sc * cell_size + int(cell_size / 2),
                                             sr * cell_size + int(cell_size / 2)),
                                             int(hunter_size / 2), 1)


def draw_goal(win, id, values):  # 画猎物，一个方框
    sc, sr = id
    dd = (cell_size - goal_size) / 2 + 1
    rect = (sc * cell_size + dd, sr * cell_size + dd, goal_size, goal_size)
    pygame.draw.rect(win, COLORS["goal"], rect)
    # 把状态机的当前状态显示出来
    draw_state(win, sc, sr, values)


def draw_state(win, sc, sr, values):  # 显示目标当前的状态
    FONTS = pygame.font.Font(pygame.font.get_default_font(), 12)
    tlst = FONTS.render("%s" % values, True, COLORS["black"])
    cxy = (sc * cell_size + goal_size - 2, sr * cell_size + goal_size - 2)
    text_rect = tlst.get_rect(center=cxy)
    win.blit(tlst, text_rect)


def draw_path_dot(win, id):  # 画逃跑路径的点
    sc, sr = id
    dd = (cell_size / 2) - 1
    rect = (sc * cell_size + dd, sr * cell_size + dd, 2, 2)
    pygame.draw.rect(win, COLORS["black"], rect)


def draw_bean(win, id):  # 画豆豆
    sc, sr = id
    dd = (cell_size / 2) - bean_size / 2
    rect = (sc * cell_size + dd, sr * cell_size + dd, bean_size, bean_size)
    pygame.draw.rect(win, COLORS["bean"], rect)


def draw_beans(graph, win):  # 画所有的豆豆
    for id in graph.beans: draw_bean(win, id)
