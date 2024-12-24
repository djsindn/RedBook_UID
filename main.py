import requests
from lxml import etree
import pandas as pd
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import threading
import time
import ttkbootstrap as ttkb


# 要访问的小红书用户主页URL，这里需替换成真实的目标用户主页地址
url = "https://www.xiaohongshu.com"

# 设置请求头，模拟浏览器访问，防止被服务器识别为异常请求而拒绝
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-bytecode-package+xml",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Connection": "keep-alive"
}

# 创建主窗口，并应用 'darkly' 主题（可更换为其他主题）
root = ttkb.Window(themename="darkly")
root.title("小红书数据获取")

# 创建一个表格用于展示数据
tree = ttk.Treeview(root, columns=("用户名", "用户号", "链接地址", "uid", "图片链接地址"), show="headings")
tree.heading("用户名", text="用户名")
tree.heading("用户号", text="用户号")
tree.heading("链接地址", text="链接地址")
tree.heading("uid", text="uid")
tree.heading("图片链接地址", text="图片链接地址")
tree.pack(padx=10, pady=10)

# 定义获取数据的函数
def get_data():
    try:
        # 发送GET请求获取页面内容
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 检查请求是否成功，若不成功则抛出异常
        html = etree.HTML(response.text)

        # 获取所有链接元素的href属性值，并提取uid
        link_elements = html.xpath('/html/body/div[1]/div[1]/div[2]/div[2]/div/div[3]/section/div/div/div/a')
        href_values = []
        uids = []
        if link_elements:
            for link in link_elements:
                href_value = link.get('href')
                href_values.append(href_value)
                # 从链接地址中提取uid，这里假设uid是在/user/profile/后面的那一串字符，以'?'为分隔界限
                parts = href_value.split('?')
                uid = parts[0].split('/')[-1]
                uids.append(uid)
        else:
            print("未通过xpath找到对应的链接元素")

        # 获取所有用户名
        username_elements = html.xpath('/html/body/div[1]/div[1]/div[2]/div[2]/div/div[3]/section/div/div/div/a/span')
        usernames = []
        if username_elements:
            for element in username_elements:
                username = element.text
                usernames.append(username)
        else:
            print("未通过xpath找到对应的元素")

        # 获取所有图片链接地址
        img_elements = html.xpath('/html/body/div[1]/div[1]/div[2]/div[2]/div/div[3]/section/div/div/div/a/img')
        img_srcs = []
        if img_elements:
            for img in img_elements:
                src_value = img.get('src')
                img_srcs.append(src_value)
        else:
            print("未通过xpath找到对应的图片元素")

        # 获取所有用户号（假设对应xpath能找到多个相关元素，这里对每个链接对应的页面分别查找提取用户号）
        all_user_ids = []
        if href_values:
            for href in href_values:
                home_url = url + href
                response_home = requests.get(home_url, headers=headers)
                response_home.raise_for_status()
                home_html = etree.HTML(response_home.text)
                id_elements = home_html.xpath('/html/body/div[1]/div[1]/div[2]/div[2]/div/div[1]/div/div[2]/div[1]/div[1]/div[2]/div[2]/span[1]')
                for id_element in id_elements:
                    id_text = id_element.text
                    if id_text:
                        if "：" in id_text:
                            user_id = id_text.split("：")[1]
                        else:
                            user_id = id_text
                        all_user_ids.append(user_id)
        else:
            print("未获取到链接地址，无法查找对应的用户号")

        # 数据处理，确保各个列表长度一致，以短的列表长度为准进行截取，使数据一一对应
        min_length = min(len(href_values), len(uids), len(usernames), len(all_user_ids), len(img_srcs))
        href_values = href_values[:min_length]
        uids = uids[:min_length]
        usernames = usernames[:min_length]
        all_user_ids = all_user_ids[:min_length]
        img_srcs = img_srcs[:min_length]

        # 创建DataFrame对象，用于存储数据并生成Excel
        my_url_group = []
        for i in href_values:
            my_url = url + i
            my_url_group.append(my_url)
        data = {
            "用户名": usernames,
            "用户号": all_user_ids,
            "链接地址": my_url_group,
            "uid": uids,
            "图片链接地址": img_srcs
        }
        return data
    except requests.RequestException as e:
        messagebox.showerror("错误", f"请求出现问题: {e}")
        return None

# 定义展示数据的函数，将获取到的数据展示在表格中
def show_data():
    # 创建等待提示窗口
    wait_window = ttkb.Toplevel(root)
    wait_window.title("等待中")
    wait_label = ttkb.Label(wait_window, text="正在获取数据，请稍候...")
    wait_label.pack(padx=10, pady=10)
    # 显示动画效果（简单的旋转加载动画，使用ttkbootstrap的Progressbar组件）
    progress = ttkb.Progressbar(wait_window, mode='indeterminate', length=200)
    progress.pack(padx=10, pady=10)
    progress.start(10)

    # 在新线程中获取数据，避免阻塞主线程
    def get_data_thread():
        data = get_data()
        if data:
            # 将字典数据转换为DataFrame
            df = pd.DataFrame(data)
            # 清空之前表格中的数据
            tree.delete(*tree.get_children())
            for index, row in df.iterrows():
                # 插入可编辑数据到表格
                tree.insert("", "end", values=(
                    row["用户名"],
                    row["用户号"],
                    row["链接地址"],
                    row["uid"],
                    row["图片链接地址"]
                ), tags=('editable',))
            # 关闭等待提示窗口
            wait_window.destroy()
        else:
            # 关闭等待提示窗口
            wait_window.destroy()

    data_thread = threading.Thread(target=get_data_thread)
    data_thread.start()

# 定义复制uid到剪贴板的函数
def copy_uid(event):
    if tree.identify_region(event.x, event.y) == "cell":
        column = tree.identify_column(event.x)
        item = tree.identify_row(event.y)
        if column == "#4":  # 'uid' 列的列标识符（从1开始计数，第4列是uid列）
            uid = tree.item(item, 'values')[3]
            root.clipboard_clear()
            root.clipboard_append(uid)
            messagebox.showinfo("提示", "已将UID复制到剪贴板")

# 定义导出到Excel的函数，并添加等待动画
def export_to_excel():
    # 创建等待提示窗口
    wait_window = ttkb.Toplevel(root)
    wait_window.title("等待中")
    wait_label = ttkb.Label(wait_window, text="正在导出数据，请稍候...")
    wait_label.pack(padx=10, pady=10)
    progress = ttkb.Progressbar(wait_window, mode='indeterminate', length=200)
    progress.pack(padx=10, pady=10)
    progress.start(10)

    # 在新线程中执行导出操作，避免阻塞主线程
    def export_data_thread():
        data = get_data()
        if data:
            df = pd.DataFrame(data)
            try:
                df.to_excel('results.xlsx', index=False)
                messagebox.showinfo("成功", "已成功生成Excel文件'results.xlsx'，包含对应的数据信息。")
            except Exception as e:
                messagebox.showerror("错误", f"导出Excel文件时出现问题: {e}")
            finally:
                # 关闭等待提示窗口
                wait_window.destroy()
        else:
            # 关闭等待提示窗口
            wait_window.destroy()

    export_thread = threading.Thread(target=export_data_thread)
    export_thread.start()


# 创建获取资源按钮
get_button = ttkb.Button(root, text="获取资源", command=show_data)
get_button.pack(padx=10, pady=5)

# 创建导出到Excel按钮
export_button = ttkb.Button(root, text="导出到Excel", command=export_to_excel)
export_button.pack(padx=10, pady=5)

# 绑定双击事件到表格，实现双击复制uid功能
tree.bind("<Double-1>", copy_uid)

root.mainloop()
