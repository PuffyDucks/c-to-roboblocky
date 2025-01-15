# ADD:
# loops
# negative numbers
# color
# if statements
# comparison
# functions
# variables
# arrays
# lists
# results
# prompts
# error checking for +=
# mod, ++ --
import xml.etree.ElementTree as ET
from clang.cindex import Index, CursorKind, Config
import yaml

from function_data import block_names

c_file_path = '/home/luna/src/barobo/c-to-blocks/example.c'
save_path = '/home/luna/Downloads'

Config.set_library_file('/usr/lib64/libclang.so.19.1.5')
index = Index.create()
tu = index.parse(c_file_path)

class Block(ET.Element):
    with open('./block_args.yaml', 'r') as file:
        args = yaml.safe_load(file)

    # *args is list of strings and blocks
    # TODO: typecheck *args and check if string or block matches with field or value
    def __init__(self, str_block_type, *args):
        block_info = Block.args.get(str_block_type)

        if not block_info:
            raise ValueError(f"Block type '{str_block_type}' not found.")
        if len(args) != len(block_info):
            raise TypeError(f"'{str_block_type}'() takes {len(block_info)} argument{'s' if len(block_info) > 1 else ''}, but recieved {len(args)}.")

        # create xml element of type 'block'
        super().__init__('block', type=str_block_type)
        
        for (arg_name, arg_type), arg_value in zip(block_info.items(), args):
            arg_element = ET.SubElement(self, arg_type, name=arg_name)
            if arg_type == "field":
                arg_element.text = str(arg_value)
            else:
                arg_element.append(arg_value)
    
    @staticmethod
    def from_node(node):
        """Builds and returns block from ast node."""
        tokens = list(node.get_tokens())
        # print(f'{node.kind} {node.spelling}')
        
        match node.kind:
            case CursorKind.FUNCTION_DECL:
                return Block.build_function_decl(node)
            case CursorKind.COMPOUND_STMT:
                return Block.build_compound_stmt(node)
            case CursorKind.PAREN_EXPR:
                child = list(node.get_children())[0]
                return Block.from_node(child)
            case CursorKind.INTEGER_LITERAL:
                return Block('math_number', tokens[0].spelling)
            case CursorKind.CALL_EXPR:
                return Block.build_expression(node)
            case CursorKind.BINARY_OPERATOR:
                return Block.build_binary_operator(node)
            case CursorKind.WHILE_STMT:
                return Block.build_while_stmt(node)
            case _:
                return None
            
    def build_compound_stmt(node):
        top = None
        bottom = None

        for child in node.get_children():
            new_block = Block.from_node(child)
            if top is None: top = new_block
            bottom = bottom.attach_next(new_block) if bottom is not None else new_block
        
        return top
    
    def build_function_decl(node):
        if node.spelling != 'main':
            raise NotImplementedError(f'Could not build function \"{node.spelling}\". Need to implement adding functions other than main')
        
        main = Block('text_comment', 'Generated with Luna\'s C-to-RoboBlocky transpiler v0.1')

        for child in node.get_children():
            if child.kind == CursorKind.COMPOUND_STMT:
                main.attach_next(Block.from_node(child))

        return main


    def build_expression(node):
        """Creates block from expression node"""
        args = []
        block_type = None

        for child in node.get_children():
            tokens = list(child.get_tokens())
            if child.kind == CursorKind.MEMBER_REF_EXPR:
                block_data = block_names[tokens[2].spelling]
                block_type = block_data.type
                if block_data.dropdown: args.append(tokens[2].spelling)
                print(f"Method called: {tokens[2].spelling}")
            elif child.kind == CursorKind.UNEXPOSED_EXPR:
                block_data = block_names[tokens[0].spelling]
                block_type = block_data.type
                if block_data.dropdown:
                    args.append(tokens[0].spelling)
                print(f"Method called: {tokens[0].spelling}")
            else:
                args.append(Block.from_node(child))    

        return Block(block_type, *args)

    def build_unary_operator(node):
        raise NotImplementedError("Unary operators not implemented.")

    def build_binary_operator(node):
        """Creates block from binary operator node"""
        arithmetic_map = {'+': 'ADD', '-': 'MINUS', '*': 'MULTIPLY', '/': 'DIVIDE'}
        comparison_map = {'==': 'EQ', '!=': 'NEQ', '<': 'LT', '<=': 'LTE', '>': 'GT', '>=': 'GTE'}
        logical_map = {'&&': 'AND', '||': 'OR'}

        # TODO: variable assignment
        if node.spelling == '=':
            children = list(node.get_children())
            return Block('variables_set', children[0].spelling, Block.from_node(children[1]))
        
        operands = [Block.from_node(operand) for operand in node.get_children()]

        if node.spelling in arithmetic_map:
            return Block('math_arithmetic', arithmetic_map[node.spelling], operands[0], operands[1])
        elif node.spelling in comparison_map:
            return Block('logic_compare', comparison_map[node.spelling], operands[0], operands[1])
        elif node.spelling in logical_map:
            return Block('logic_operation', logical_map[node.spelling], operands[0], operands[1])
        raise NotImplementedError(f"Binary operator {node.spelling} not implemented.")

    def build_while_stmt(node):
        children = [Block.from_node(child) for child in node.get_children()]
        return Block('controls_whileUntil', 'WHILE', children[0], children[1])

    def attach_next(self, child_block):
        """
        Appends child block wrapped in 'next' element. Returns bottom block.

        In RoboBlocky, attaches the child block directly below the parent block. 
        """
        if child_block is None:
            return self

        element_next = ET.SubElement(self, 'next')
        element_next.append(child_block)
        return child_block
    
def from_tu(node):
    """
    Sets up root from tu cursor, and initiates building main function. 
    """
    root = ET.Element('xml', xmlns='http://www.w3.org/1999/xhtml')

    for child in node.get_children():
        if child.kind == CursorKind.FUNCTION_DECL:
            root.append(Block.build_function_decl(child))

    root.insert(0, ET.Comment(" RoboBlockly hash lines color: #FFFFFF "))
    root.insert(0, ET.Comment(" RoboBlockly tics lines color: #FFFFFF "))
    root.insert(0, ET.Comment(" RoboBlockly background color: #FFFFFF "))
    root.insert(0, ET.Comment(f" RoboBlockly grid: [{0}, {10}] by [{0}, {10}] "))
    root.insert(0, ET.Comment(" RoboBlockly gridView: Small View "))
    root.insert(0, ET.Comment(" Code generated by RoboBlockly v2.5 "))
    return root


### MAIN ###
root = from_tu(tu.cursor)

xml_tree = ET.ElementTree(root)
ET.indent(xml_tree, space='  ', level=0)
xml_tree.write(f'{save_path}/convert.xml', encoding='utf-8')
print(f"XML file generated.")