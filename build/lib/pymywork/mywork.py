import pandas as pd
import warnings
from tqdm import tqdm
import os

# import swifter
# from numba import jit
warnings.filterwarnings('ignore')


# 获取数据库数据
def get_mysql_table(name: str, table: str):
    """
    链接Mysql
    :param table: 表名
    :param name: 库名
    :return: df
    """
    # 获取数据库数据
    from sqlalchemy import create_engine
    local_con = create_engine(f'mysql+pymysql://root:qianjiang@localhost:3306/{name}')
    df = pd.read_sql_table(table, local_con)
    return df


def get_mysql_con(name: str):
    """
    链接Mysql
    :param name: 库名
    :return: local_con
    """
    # 获取数据库数据
    from sqlalchemy import create_engine
    local_con = create_engine(f'mysql+pymysql://root:qianjiang@localhost:3306/{name}')
    return local_con


def get_file_folder():
    """
    获取文件夹路径
    :return: path
    """
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askdirectory()
    return path


def get_data():
    """
    获取单个文件路径
    :return: path
    """
    # 获取文件路径
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askopenfilename()
    return path


def get_datas():
    """
    获取多个文件路径
    :return:  path of tuple
    """
    # 获取多文件路径
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askopenfilenames()
    return path


def jz_card_to_all():
    """
    合并文件夹下经侦调取的银行卡，原始数据为易明细信息、账户信息、人员信息的csv文件
    报错:No columns to parse from file 有空文件中无表头
    :return: file :一个字典，包含三张表，交易明细信息、账户信息、人员信息
    """
    # 合并经侦银行卡
    import re
    path = get_file_folder()
    deal, staff, account, contact, location, compulsion, task = [[], [], [], [], [], [], []]  # 定义list
    file = {"交易明细": deal,
            "账户信息": account,
            "人员信息": staff,
            '人员联系方式信息': contact,
            '人员住址信息': location,
            '强制措施信息': compulsion,
            '任务信息': task}
    # 创建字典，value为上面的list
    filename = os.listdir(path)
    for i in filename:
        for j in file.keys():  # 字典key循环
            if re.search(j, i):  # 匹配关键字
                file[j].append(i)  # 添加到字典value的list

    for i in file.keys():
        total = pd.DataFrame()
        for j in file[i]:  # 循环字典value里的list
            b = pd.read_csv(path + '/' + j, encoding="GB18030", dtype=str)
            # encoding = "gbk"使用gbk编码读csv
            total = pd.concat([b, total], ignore_index=True)
        file[i] = total  # 将合并表赋值给对应value
    return file


def excel_to_all(extend: str = 'xlsx'):
    """
    合并文件夹下表头相同excel数据
    :param extend: xlsx、xls、csv 默认xlsx
    :return: total: 合并后dataframe
    """
    path = get_file_folder()
    # 同表头文件合并（治安银行卡）
    filename = os.listdir(path)
    total = pd.DataFrame()
    if extend == 'xlsx' or extend == 'xls':
        for j in tqdm(filename):
            b = pd.read_excel(path + '/' + j, dtype=str)
            total = pd.concat([b, total], ignore_index=True)
    if extend == 'csv':
        for j in filename:
            b = pd.read_csv(path + '/' + j, encoding="gbk", dtype=str)
            total = pd.concat([b, total], ignore_index=True)
    return total


def sheet_to_all(sheet: str):
    """
    合并文件夹下指定xlsx文件sheet
    :param sheet: 指定sheet名
    :return: data: 合并表
    """

    path = get_file_folder()
    list1 = os.listdir(path)
    data = pd.DataFrame()
    for i in list1:
        b = pd.read_excel(f"{path}/" + i, sheet_name=sheet, dtype=str)
        b = b.where(b.notnull(), '')
        data = pd.concat([b, data], ignore_index=True)
    return data


def pivot_table_deal_distinct():
    """
    对透视文件xslx，主对端银行卡都有记录，借贷重复去重
    :return: df:双向去重后数据表
    """
    path = get_data()
    df = pd.read_excel(path)
    df["借"] = pd.to_numeric(df["借"])
    df["贷"] = pd.to_numeric(df["贷"])
    for row in tqdm(df.index):
        # 筛选主对端相反的数据 若用双循环遍历较慢，因此用相反的账号做两个筛选，最后取交集速度大幅加快
        data = df[(df['查询账号'] == df.loc[row, '对方账号卡号']) & (df['对方账号卡号'] == df.loc[row, '查询账号'])]
        if data.empty:
            continue

        else:
            # data.index为列表，包含切片内容的行号与数据类型
            # print(data.index)
            if df.loc[row]['贷'] >= df.loc[data.index[0], '借']:
                df.loc[data.index[0], '借'] = None
            else:
                df.loc[row, '贷'] = None

            if df.loc[row]['借'] >= df.loc[data.index[0], '贷']:
                df.loc[data.index[0], '贷'] = None
            else:
                df.loc[row, '借'] = None
    return df


def location_extract(lie: str):
    """
    地址信息标准化提取
    :param lie: 需要标准化的地址列
    :return: df: 标准化的表
    """
    import jionlp as jio
    path = get_data()
    df = pd.read_excel(path, dtype=str)
    df = pd.concat([df, pd.DataFrame(columns=['省', '市', '区', '详细'])])
    for i in tqdm(df.index):
        df['省'][i] = jio.parse_location(df[lie][i])['province']
        df['市'][i] = jio.parse_location(df[lie][i])['city']
        df['区'][i] = jio.parse_location(df[lie][i])['county']
        df['详细'][i] = jio.parse_location(df[lie][i])['detail']
    return df


def agent_under_people(uid: str, invite_id: str):
    """
    代理关系表计算会员伞下人数及具体伞下会员ID
    :param uid: 会员ID列
    :param invite_id: 上级ID列
    :return: df2 : 伞下会员表
    """
    # 读取数据框
    df = pd.read_excel(get_data(), dtype='str')
    df2 = pd.DataFrame(columns=['ID', '伞下人数'])
    dict_members = {}

    def count_subordinates(userid, members_list):
        count = 0
        subordinates = df[df[invite_id] == userid][uid]
        members_list.extend(list(subordinates))
        count += len(subordinates)
        for subordinate in subordinates:
            count += count_subordinates(subordinate, members_list)[0]
        return count, members_list

        # 计算每个用户ID下级各级成员的数量

    for user_id in tqdm(df[uid]):
        members = []
        result = count_subordinates(user_id, members)
        total_count = result[0]
        dict_members[user_id] = result[1]
        # print(f"用户ID {user_id} 下级各级成员数量: {total_count}")
        df2.loc[len(df2.index)] = [user_id, total_count]
    df2['ID'] = df2['ID'].astype("str")
    dict_members = [{'ID': k, 'value': v} for k, v in dict_members.items()]
    df3 = pd.DataFrame(dict_members).astype("str")
    df2 = pd.merge(df2, df3, on='ID')
    return df2


def agent_under_layer(uid: str, invite_id: str):
    """
    代理关系表计算会员向下还有多少层
    :param uid: 会员ID列
    :param invite_id: 上级ID列
    :return: df2: 向下级层级表
    """
    # 加载数据到DataFrame
    df = pd.read_excel(get_data(), dtype='str')

    # 递归函数计算层级
    def calculate_level(df1, id1, level=1):
        # 找到当前id的所有下级id
        sub_ids = df1[df1[invite_id] == id1][uid]

        # 如果没有下级id，则返回当前层级
        if len(sub_ids) == 0:
            return level

        # 否则，递归计算下级id的层级，并返回最大层级
        return max(calculate_level(df, sub_id, level + 1) for sub_id in sub_ids)

    # 计算每个id的层级
    tqdm.pandas(desc='apply')
    df['层级'] = df[uid].progress_apply(lambda x: calculate_level(df, x))
    df2 = df[[uid, '层级']]
    df2[uid] = df2[uid].astype("str")
    return df2


def agent_up_layer(uid: str, invite_id: str):
    """
    代理关系表计算向上层级及路径上的会员ID
    :param uid: 会员ID列
    :param invite_id: 上级ID列
    :return: df: 向上层级表
    """

    def calculate_level(user_id, uids, invite_uids):
        # 找到用户ID对应的上级ID
        superior = df[df[uids] == user_id][invite_uids]
        # 如果上级ID为空，则说明已经到达最上级，返回空列表
        if superior.empty:
            return []

        parent_id = superior.values[0]

        # if pd.isnull(parent_id):
        #     return []

        # 递归调用函数，计算上级ID的上级ID
        parents = calculate_level(parent_id, uids, invite_uids)

        # 返回上级ID的上级ID列表，加上当前上级ID
        return parents + [parent_id]

    df = pd.read_excel(get_data(), dtype='str')
    tqdm.pandas(desc='apply')
    df['上级'] = df[uid].progress_apply(lambda x: calculate_level(x, uid, invite_id))
    df['账户层级'] = df['上级'].apply(lambda x: len(x))
    df = df[[uid, '账户层级', '上级']].astype('str')

    return df


def files_classify():
    """
    以移动清单移动文件，需要准备一个文件清单包含需要移动的文件名和移动后的文件夹。
    也可完成每个文件建一个文件夹
    """
    # 读取清单.xlsx
    checklist = pd.read_excel(get_data(), dtype='str')

    # 读取需要整理的文件夹
    folder_path = get_file_folder()

    # 遍历清单中的每一行
    for index, row in checklist.iterrows():
        # 获取文件名和文件夹名
        file_name = row[0]
        folder_name = row[1]
        # 在需要整理的文件夹下新建文件夹
        new_folder_path = os.path.join(folder_path, folder_name)
        if not os.path.exists(new_folder_path):
            os.makedirs(new_folder_path)

        # 遍历需要整理的文件夹下的文件
        for file in os.listdir(folder_path):
            # 如果文件名包含清单中的字符串，则移动到相应文件夹
            if file_name in file:
                old_file_path = os.path.join(folder_path, file)
                new_file_path = os.path.join(new_folder_path, file)
                os.rename(old_file_path, new_file_path)


class High_risk_males:

    def __init__(self):
        """构造函数"""
        self.mian_df = pd.DataFrame(
            columns=['姓名', '身份证', '身份证归属地', '银行卡', '支付宝', '手机号', '手机归属地', '常用IP',
                     '常用交易网点（借）', '来源案件', '案件类型', '案件角色', '案件我方处理结果'])
        self.opponent_df = pd.DataFrame(columns=['案件', '主端账号', '对端账号', '对端姓名'])


def get_encoding():
    """
    二进制方式读取，获取字节数据，检测类型
    :return: encod: 文件编码list
    """
    import chardet
    path = get_file_folder()
    list1 = os.listdir(path)
    encod = []
    for i in tqdm(list1):
        with open(f"{path}/" + i, 'rb') as f:
            encod.append(chardet.detect(f.read())['encoding'])
    return encod


def heat_map(locations: dict):
    """
    绘制热力图
    :param locations: 省名及数值如{'上海': 23, '北京': 45, '合肥':16}
    :return: c: 外部c.render(xxx.html)导出
    """
    from pyecharts import options as opts
    from pyecharts.charts import Geo
    from pyecharts.globals import ChartType
    # from pyecharts.render import make_snapshot
    # from snapshot_phantomjs import snapshot
    # import os

    # 基础数据
    # keys = ['上海', '北京', '合肥', '哈尔滨', '广州', '成都', '无锡', '杭州', '武汉', '深圳', '西安', '郑州', '重庆', '长沙', '贵阳', '乌鲁木齐']
    # values = [40.07, 13, 47, 21, 3.53, 4.37, 1.38, 4.29, 4.1, 1.31, 3.92, 4.47, 2.40, 3.60, 1.2, 3.7]
    location_dict = locations

    c = (
        Geo()
        .add_schema(maptype="china")
        .add(
            "",
            # [list(z) for z in zip(keys, values)],
            [list(z) for z in zip(location_dict.keys(), location_dict.values())],
            type_=ChartType.EFFECT_SCATTER,
        )
        .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
        .set_global_opts(title_opts=opts.TitleOpts(title=""),
                         visualmap_opts=opts.VisualMapOpts(
                             type_="size",  # 映射大小 ,color 映射颜色
                             max_=100,
                             min_=20,
                             pos_bottom='50',
                             pos_right='0'
                         )
                         )
        # .render("vv.html")
    )
    # 打开html
    # os.system("vv.html")
    # 转图片
    # make_snapshot(snapshot,c,"vv.png")

    # 返回c 外部生成图heat_map().render('sss.html')
    return c


def table_splitting(df_df, lie: str):
    """
    按某列拆分文件
    :param df_df: 需要拆分的数据
    :param lie: 拆分列
    """
    df = df_df
    path = get_file_folder()
    card_list = list(set(df[lie]))
    for card in tqdm(card_list):
        card_data = df[df[lie] == card]
        card_data.to_excel(path + '/' + card + '.xlsx', index=False)


def multiple_sheet_to_all(sheetname_list: list = None):
    """
    合并多sheet的excel
    :param sheetname_list: sheet名列表
    :return: dict_all: 存放多表的字典
    """
    if sheetname_list is None:
        sheetname_list = ['注册信息', '登录日志', '账户明细']
    path = get_file_folder()
    filename = os.listdir(path)

    dict_all = {}
    for j in sheetname_list:
        data = pd.DataFrame()
        for i in tqdm(filename):
            b = pd.read_excel(path + "/" + i, sheet_name=j, dtype=str)
            b = b.where(b.notnull(), '')
            data = pd.concat([b, data], ignore_index=True)
        dict_all[j] = data

    return dict_all
