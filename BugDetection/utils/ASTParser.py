from tree_sitter import Language, Parser
from config import TREE_SITTER_C


class ASTParser:
    def __init__(self):
        pass
    
    @staticmethod
    def tree_sitter_init():
        Language.build_library(
            "build/my-languages.so",
            [TREE_SITTER_C],
        )

        C_LANGUAGE = Language("build/my-languages.so", "c")
        parser = Parser()
        parser.set_language(C_LANGUAGE)
        return parser
    
    @staticmethod
    def get_func_name_from_def(code):
        parser = ASTParser.tree_sitter_init()
        tree = parser.parse(bytes(code, "utf8"))
        funcs = ASTParser.find_node_by_type(tree,"function_declarator")
        if len(funcs) == 0:
            return ''

        return ASTParser.get_node_content(funcs[0].child_by_field_name("declarator"), code)

    @staticmethod
    def find_node_by_type(node, node_type):
        cursor = node.walk()
        if type(node_type) == str:
            node_type = [node_type]
        node_lst = []
        while True:
            if cursor.node.type in node_type:
                node_lst.append(cursor.node)
            if not cursor.goto_first_child():
                while not cursor.goto_next_sibling():
                    if not cursor.goto_parent():
                        return node_lst
                
    @staticmethod        
    def get_node_content(node, code):
        return code[node.start_byte : node.end_byte]
