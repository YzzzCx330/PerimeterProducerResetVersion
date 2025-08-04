from mcdreforged.api.all import *
from minecraft_data_api import get_player_coordinate, get_player_dimension, get_server_player_list
import time
import math
import re

PLUGIN_METADATA = {
    'id': 'pp',
    'version': '1.0.0',
    'name': 'PerimeterProducer',
    'description': 'A plugin with multiple functions',
    'author': 'WalkerTian',
    'link': 'https://github.com/Walkersifolia/PerimeterProducer',
    'dependencies': {
		'minecraft_data_api': '*'
	}
}

class PlayerPos(TypedDict):
    positon: Tuple[int, int, int]
    dimension: str

DELAY = 0.2
Prefix = "!!pp"
CHUNK = 16
ABORT = False
WORKING = False
NEED_COMMIT = False
TIMER = False
X = None
Z = None
SIZE = None
p1 = None
p2 = None
p3 = None
p4 = None

def start_timer(server):
    global NEED_COMMIT, ABORT, WORKING
    time.sleep(20)
    if NEED_COMMIT and not WORKING and TIMER:
        NEED_COMMIT = False
        ABORT = True
        server.say("§c20秒内未确认，操作自动取消")
        TIMER = False

@new_thread(f"{PLUGIN_ID}-player_pos")
def get_player_pos(player: str, timeout: int = 5) -> dict:
    pos = get_player_coordinate(player)
    dimension = get_player_dimension(player)
    player_pos = {
        "position": (int(pos.x), int(pos.y), int(pos.z)),
        "dimension": dimension
    }
    if not player_pos:
        return

def on_info(server, info):
    global Prefix, DELAY
    global CHUNK, ABORT, WORKING, NEED_COMMIT
    global SIZE, X, Z
    global p1, p2, p3, p4
    global TIMER
    content = info.content
    cmd = content.split()
    if len(cmd) == 0 or cmd[0] != Prefix:
        return
    del cmd[0]
    # !!perimeter abort
    if len(cmd) == 1 and cmd[0] == "abort":
        if not WORKING and not NEED_COMMIT:
            server.reply(info, "§c没有需要中断的操作")
            return
        ABORT = True
        NEED_COMMIT = False
        server.reply(info, "§c终止操作！")
        return
    # !!perimeter abort <length> <width>
    if len(cmd) == 2 and cmd[0] == "make":
        player = info.player
        result = player_pos(player)
        pos = result.position
        if len(pos) != 3:
            server.say(info, "§c在线玩家才能使用该指令！")
            return
        if WORKING:
            server.reply(info, "§c当前正在清理，请等待清理结束！")
        try:
            size_input = int(cmd[1])
        except ValueError:
            server.reply(info, "§c你输入的不是数字！")
            return
        if cmd[1] % 2 == 1 and cmd[1] >= 3:
            SIZE = (cmd[1] - 1) / 2
        else:
            server.reply(info, "§c空置域大小必须为一个大于等于3的奇数！")
        X = pos[0] // 16
        Z = pos[2] // 16
        p1 = (X - SIZE) * CHUNK
        p2 = (X + SIZE) * CHUNK + 15
        p3 = (Z + SIZE) * CHUNK
        p4 = (Z - SIZE) * CHUNK + 15
        
        NEED_COMMIT = True
        TIMER = True
        server.reply(info, "§a请输入§6{} commit§a确认操作！".format(Prefix))

        if TIMER_THREAD is None or not TIMER_THREAD.is_alive():
            TIMER_THREAD = threading.Thread(target=start_timer, args=(server,))
            TIMER_THREAD.start()
        return

    if len(cmd) == 1 and cmd[0] == "commit":

        if not NEED_COMMIT:
            server.reply(info, "§c没有需要确认的操作")
            return

        server.say("§a开始操作！")
        NEED_COMMIT = False
        TIMER = False

        server.execute("carpet fillLimit 2000000")
        server.execute("carpet fillUpdates false")
        
        WORKING = True
        for i in range(0, 375):
            if ABORT:
                ABORT = False
                WORKING = False
                server.reply(info, "§c终止操作！")
                break
            y = 311 - i
            dimension = result.dimension
            command = "execute at {} run fill {} {} {} {} {} {} air".format(dimension, p1, y, p3, p2, y, p4)
            server.say("正在替换第{}层".format(y))
            server.execute(command)
            time.sleep(DELAY)
        WORKING = False
        server.say("§a操作完成！")

def on_load(server: PluginServerInterface, old):
    server.register_help_message('!!pp', '快速生成空置域')
    server.logger.info('插件已加载！')
