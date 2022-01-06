#coding=utf-8
import javalang
from javalang import *
import os
import traceback

'''
适用windows

准备条件：
1.下载FernFlower.jar和procyon-decompiler.jar并放置到D盘根目录
2.pip install javalang
3.安装unzip
'''

def decomplier(file):
    """
    反编译
    :param file:
    :return:
    """
    decompile_tmp = 'D:\\decompile_tmp'
    cmd = "java -jar d:\\FernFlower.jar " + file + " " + decompile_tmp + ' > nul 2>&1'
    print cmd
    os.system(cmd)

    jar_file_name = file.split('\\')[-1]
    #print jar_file_name
    jar_file_path = decompile_tmp + '\\' + jar_file_name

    target_dir = jar_file_name.split('.')[:-1]
    source_dir = '.'.join(target_dir)
    source_dir = decompile_tmp + '\\' + source_dir
    unzip_cmd = "unzip -o " + jar_file_path + " -d " + source_dir + ' > nul 2>&1'
    #print unzip_cmd
    if os.system(unzip_cmd) == 0:
        return source_dir
    cmd = 'java -jar d:\\procyon-decompiler.jar ' + file + ' -o ' + source_dir + ' > nul 2>&1'
    print cmd
    if os.system(cmd) == 0:
        return source_dir
    print '#####' + file + ' decompile fail'
    return ''
    
def get_class_declaration(root):
    """
    筛选出符合条件的类
    :param root:
    :return:
    """
    class_list = []
    black_interface = ("DataSource", "RowSet")
    for node in root.types:
        # 非类声明都不分析
        if isinstance(node, tree.ClassDeclaration) is False:
            continue
        # 判断是否继承至classloader
        if node.extends is not None and node.extends.name == "ClassLoader":
            continue
        # 判断是否实现被封禁的接口
        interface_flag = False
        if node.implements is None:
            node.implements = []
        for implement in node.implements:
            if implement.name in black_interface:
                interface_flag = True
                break
        if interface_flag is True:
            continue
        # 判断是否存在无参的构造函数
        constructor_flag = False
        for constructor_declaration in node.constructors:
            if len(constructor_declaration.parameters) == 0:
                constructor_flag = True
                break
        if constructor_flag is False:
            continue
        class_list.append(node)
    return class_list
    
def get_class_extends_xx(root, xx):
    class_list = []
    for node in root.types:
        # 非类声明都不分析
        if isinstance(node, tree.ClassDeclaration) is False:
            continue
        # 判断是否继承至xx
        if node.extends is not None and node.extends.name == xx:
            # 判断是否存在无参的构造函数
            constructor_flag = False
            for constructor_declaration in node.constructors:
                if len(constructor_declaration.parameters) == 0:
                    constructor_flag = True
                    break
            if constructor_flag is False:
                continue
            class_list.append(node.name)
    return class_list
    
def ack(method_node):
    """
    1、是否调用的lookup 方法，
    2、lookup中参数必须是变量
    3、lookup中的参数必须来自函数入参，或者类属性
    :param method_node:
    :return:
    """
    target_variables = []
    for path, node in method_node:
        # 是否调用lookup 方法
        if isinstance(node, tree.MethodInvocation) and node.member == "lookup":
            # 只能有一个参数。
            if len(node.arguments) != 1:
                continue
            # 参数类型必须是变量，且必须可控
            arg = node.arguments[0]
            if isinstance(arg, tree.Cast):    # 变量 类型强转
                target_variables.append(arg.expression.member)
            if isinstance(arg, tree.MemberReference):  # 变量引用
                target_variables.append(arg.member)
            if isinstance(arg, tree.This):       # this.name， 类的属性也是可控的
                return True
    if len(target_variables) == 0:
        return False
    # 判断lookup的参数，是否来自于方法的入参，只有来自入参才认为可控
    for parameter in method_node.parameters:
        if parameter.name in target_variables:
            return True
    return False
    
filePaths = []
def iterate_dir(path, suffix):
    parents = os.listdir(path)
    for parent in parents:
        child = os.path.join(path,parent)
        if child == '.' or child == '..':
            continue
        if os.path.isdir(child):
            iterate_dir(child, suffix)
        else:
            #print(child)
            if child.endswith(suffix):
                filePaths.append(child)
                
                
def find_gadget(jardir):
    global filePaths
    iterate_dir(jardir, ".jar")
    jarFilePathList = filePaths
    #print jarFilePathList
    for jarFilePath in jarFilePathList:
        try:
            dir = decomplier(jarFilePath)
            if dir == '':
                continue
            filePaths = []
            iterate_dir(dir, ".java")
            #print filePaths
            for javaFile in filePaths:
                with open(javaFile) as fileObj:
                    content = fileObj.read()
                    fileObj.close()
                    if "InitialContext(" not in content:
                        continue
                    #print content
                    root = javalang.parse.parse(content)
                    class_list = get_class_declaration(root)
                    #print class_list
                    for elem in class_list:
                        for path_1, node_1 in elem:
                            if isinstance(node_1, tree.MethodDeclaration):
                                if ack(node_1) is True:
                                    print "***** Found in " + javaFile + ", method:" +node_1.name
        except Exception as e:
            print e
            traceback.print_exc()
            
def find_class(jardir):
    global filePaths
    iterate_dir(jardir, ".jar")
    jarFilePathList = filePaths
    #print jarFilePathList
    for jarFilePath in jarFilePathList:
        try:
            dir = decomplier(jarFilePath)
            if dir == '':
                continue
            filePaths = []
            iterate_dir(dir, ".java")
            #print filePaths
            for javaFile in filePaths:
                with open(javaFile) as fileObj:
                    content = fileObj.read()
                    fileObj.close()
                    #print content
                    root = javalang.parse.parse(content)
                    class_list = get_class_extends_xx(root, 'Exception')
                    if(len(class_list)>0):
                        print "***** Found in " + javaFile
                        print class_list
        except Exception as e:
            print e
            traceback.print_exc()
#find_gadget("C:\\Users\\f00496378\\.m2\\repository\\com\\huawei")
#find_gadget("C:\\Users\\f00496378\\.m2\\repository")
#find_gadget("D:\\TEST_JAR")
#find_class("D:\\TEST_JAR")
find_class("C:\\Users\\f00496378\\.m2\\repository")