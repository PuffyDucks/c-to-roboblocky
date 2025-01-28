# ADD:
# loops
# color
# strings
# if statements
# functions
# arrays
# lists
# results
# prompts
# error checking for +=
# mod, ++ --
import xml.etree.ElementTree as ET
from clang.cindex import Index, CursorKind, Config
import yaml

c_file_path = '/home/luna/src/barobo/c-to-blocks/example.c'
save_path = '/home/luna/Downloads'

Config.set_library_file('/usr/lib64/libclang.so.19.1.5')
index = Index.create()
tu = index.parse(c_file_path)

class Block(ET.Element):
    with open('./block_args.yaml', 'r') as file:
        args = yaml.safe_load(file)
    with open('./method_blocks.yaml', 'r') as file:
        methods = yaml.safe_load(file)

    # *args is list of strings and blocks
    # TODO: typecheck *args and check if string or block matches with field or value
    def __init__(self, str_block_type, *args):
        block_info = Block.args.get(str_block_type)

        if not block_info:
            raise ValueError(f"Block type '{str_block_type}' could not be found in block_args.yaml.")
        if len(args) != len(block_info):
            raise TypeError(f"'{str_block_type}'() takes {len(block_info)} argument{'s' if len(block_info) > 1 else ''}, but recieved {len(args)}.")

        # create xml element of type 'block'
        super().__init__('block', type=str_block_type)
        self.stack_bottom = self
        
        for (arg_name, arg_type), arg_value in zip(block_info.items(), args):
            arg_element = ET.SubElement(self, arg_type, name=arg_name)
            if arg_type == "field":
                arg_element.text = str(arg_value)
            else:
                arg_element.append(arg_value)
    
    @staticmethod
    def from_node(node):
        """Builds and returns block from ast node."""
        print(f'{node.kind} {node.spelling}')
        cursor_kind_map = {
            CursorKind.FUNCTION_DECL: Block.build_function_decl,
            
            CursorKind.COMPOUND_STMT: Block.build_compound_stmt,
            CursorKind.PAREN_EXPR: Block.build_paren_expr,
            CursorKind.CALL_EXPR: Block.build_expression,
            CursorKind.DECL_REF_EXPR: Block.build_decl_ref_expr,
            CursorKind.UNEXPOSED_EXPR: Block.build_unexposed_expr,

            CursorKind.DECL_STMT: Block.build_decl_stmt,

            CursorKind.UNARY_OPERATOR: Block.build_unary_operator,
            CursorKind.BINARY_OPERATOR: Block.build_binary_operator,
            CursorKind.INTEGER_LITERAL: Block.build_number_literal,
            CursorKind.FLOATING_LITERAL: Block.build_number_literal,
            CursorKind.WHILE_STMT: Block.build_while_stmt
        }

        if cursor_kind_map.get(node.kind):
            return cursor_kind_map.get(node.kind)(node)
                    
        raise NotImplementedError(f"Node type {node.kind} is not supported.")

    def build_function_decl(node):
        if node.spelling != 'main':
            raise NotImplementedError(f"Could not build function \"{node.spelling}\". Need to implement adding functions other than main.")
        
        main = Block('text_comment', "Generated with Luna\'s C-to-RoboBlocky transpiler v0.1")

        for child in node.get_children():
            if child.kind == CursorKind.COMPOUND_STMT:
                main.attach(Block.from_node(child))

        return main
      
    def build_compound_stmt(node):
        top = None
        bottom = None

        for child in node.get_children():
            new_block = Block.from_node(child)
            if top is None: top = new_block
            bottom = bottom.attach(new_block) if bottom is not None else new_block.stack_bottom
        
        top.stack_bottom = bottom
        return top

    def build_paren_expr(node):
        child = list(node.get_children())[0]
        return Block.from_node(child)

    def build_expression(node):
        """Creates block from expression node"""
        block_type = None
        args = []

        # TODO: make the token not hard coded
        for child in node.get_children():
            tokens = list(child.get_tokens())
            method_name = None

            if child.kind == CursorKind.MEMBER_REF_EXPR:
                method_name = tokens[2].spelling
            elif child.kind == CursorKind.UNEXPOSED_EXPR:
                method_name = tokens[0].spelling
            else:
                args.append(Block.from_node(child))    

            if method_name is not None:
                if not Block.methods.get(method_name):
                    raise ValueError(f"Method \"{method_name}\" could not be found in method_blocks.yaml.")
                method_data = Block.methods.get(method_name)
                block_type = method_data['block_type']

                if method_data['dropdown']: args.append(method_name)
                print(f"Method called: {method_name}")

        return Block(block_type, *args)

    def build_unary_operator(node):
        token = list(node.get_tokens())[0]
        child = list(node.get_children())[0]

        # TODO: use math_change to implement ++, --, +=, -=
        if token.spelling == '!':
            return Block('logic_negate', Block.from_node(child))
        elif token.spelling == '-':
            return Block('math_negative', Block.from_node(child))
        raise NotImplementedError(f"Unary operator {token.spelling} is not supported.")

    def build_binary_operator(node):
        """Creates block from binary operator node"""
        arithmetic_map = {'+': 'ADD', '-': 'MINUS', '*': 'MULTIPLY', '/': 'DIVIDE'}
        comparison_map = {'==': 'EQ', '!=': 'NEQ', '<': 'LT', '<=': 'LTE', '>': 'GT', '>=': 'GTE'}
        logical_map = {'&&': 'AND', '||': 'OR'}

        # variable assignment
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
        raise NotImplementedError(f"Binary operator {node.spelling} is not supported.")

    def build_number_literal(node):
        """Creates block from integer or floating literal node"""
        tokens = list(node.get_tokens())
        return Block('math_number', tokens[0].spelling)

    def build_while_stmt(node):
        """Creates block from while statement node"""
        children = [Block.from_node(child) for child in node.get_children()]
        return Block('controls_whileUntil', 'WHILE', children[0], children[1])
    
    def build_decl_ref_expr(node):
        referenced = node.referenced
        if referenced.kind == CursorKind.VAR_DECL:
            return Block('variables_get', referenced.spelling)
        else:
            raise NotImplementedError(f"Declaration to {referenced.kind} is not supported.")

    def build_unexposed_expr(node):
        child = list(node.get_children())[0]
        return Block.from_node(child)

    def build_var_decl(node):
        """Creates block from variable declaration node"""
        children = list(node.get_children())
        if children: 
            return Block('variables_set_with_type', node.type.spelling, node.spelling, Block.from_node(children[0]))
        else: 
            return Block('variables_create_with_type', node.type.spelling, node.spelling)

    def build_decl_stmt(node):
        children = list(node.get_children())
        top = None
        bottom = None

        for child in children:
            if (child.kind != CursorKind.VAR_DECL):
                raise NotImplementedError(f"Declaration to {child.kind} is not supported.")
            
            new_block = Block.build_var_decl(child)
            if top is None: top = new_block
            bottom = bottom.attach(new_block) if bottom is not None else new_block.stack_bottom
        
        top.stack_bottom = bottom
        return top

    def attach(self, child_block):
        """
        Appends child block wrapped in 'next' element. Returns bottom block.

        In RoboBlocky, attaches the child block directly below the parent block. 
        """
        if child_block is None:
            return self

        element_next = ET.SubElement(self, 'next')
        element_next.append(child_block)
        return child_block.stack_bottom
    
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