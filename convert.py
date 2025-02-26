# ADD:
## functions
# color, hard code a function to check for valid string or color returning method 
# strings
# math constants
## arrays
# lists
# results
# prompts
# mod, +=, ++, --, ? altho im not sure if ? even works in roboblocky
import xml.etree.ElementTree as ET
from clang.cindex import Index, CursorKind, Config
import yaml

c_file_path = '/home/luna/src/barobo/c-to-blocks/example.c'
save_path = '/home/luna/Downloads'
Config.set_library_file('/usr/lib64/libclang.so.19.1.5')

class Block(ET.Element):
    with open('./block_args.yaml', 'r') as file:
        args = yaml.safe_load(file)
    with open('./method_blocks.yaml', 'r') as file:
        methods = yaml.safe_load(file)

    # TODO: typecheck *args and check if string or block matches with field or value
    def __init__(self, block_type: str, *args):
        """
        Build block from str block_type and *args. *args is list of strings for fields and blocks for values.
        """
        block_info = Block.args.get(block_type)

        # block_info modifications with mutations 
        if block_type == "controls_if":
            block_info = Block.create_if_info(args[0])

        if not block_info:
            raise ValueError(f"Block type '{block_type}' could not be found in block_args.yaml.")
        if len(args) != len(block_info):
            raise TypeError(f"'{block_type}'() takes {len(block_info)} argument{'s' if len(block_info) > 1 else ''}, but recieved {len(args)}.")

        # create xml element of type 'block'
        super().__init__('block', type=block_type)
        self.stack_bottom = self
        
        for (arg_name, arg_type), arg_value in zip(block_info.items(), args):
            if arg_type == 'mutation': 
                self.append(arg_value)
                continue
            
            arg_element = ET.SubElement(self, arg_type, name=arg_name)
            if arg_type == 'field':
                arg_element.text = str(arg_value)
            elif arg_value is not None:
                arg_element.append(arg_value)
    
    @staticmethod
    def from_node(node):
        """Builds and returns block from ast node."""
        print(f'{node.kind} {node.spelling}')
        cursor_kind_map = {
            CursorKind.FUNCTION_DECL: Block.build_function_decl,
            CursorKind.RETURN_STMT: Block.build_return_stmt,
            
            CursorKind.COMPOUND_STMT: Block.build_compound_stmt,
            CursorKind.NULL_STMT: Block.build_null_stmt,
            CursorKind.PAREN_EXPR: Block.build_paren_expr,
            CursorKind.CALL_EXPR: Block.build_expression,
            CursorKind.DECL_REF_EXPR: Block.build_decl_ref_expr,
            CursorKind.UNEXPOSED_EXPR: Block.build_unexposed_expr,

            CursorKind.DECL_STMT: Block.build_decl_stmt,

            CursorKind.UNARY_OPERATOR: Block.build_unary_operator,
            CursorKind.BINARY_OPERATOR: Block.build_binary_operator,
            CursorKind.INTEGER_LITERAL: Block.build_number_literal,
            CursorKind.FLOATING_LITERAL: Block.build_number_literal,

            CursorKind.WHILE_STMT: Block.build_while_stmt,
            CursorKind.FOR_STMT: Block.build_for_stmt,
            CursorKind.IF_STMT: Block.build_if_stmt
        }

        if cursor_kind_map.get(node.kind):
            return cursor_kind_map.get(node.kind)(node)
                    
        raise NotImplementedError(f"Node type {node.kind} is not supported.")

    def build_function_decl(node):
        # Generate the main function without a function block 
        if node.spelling == 'main':
            main_stack = Block('text_comment', "Generated with Luna\'s C-to-RoboBlocky transpiler v0.3")        
            for child in node.get_children():
                if child.kind == CursorKind.COMPOUND_STMT:
                    main_stack.attach(Block.from_node(child))
            return main_stack
        
        # Other functions
        parameters = []
        statement = None
        for child in node.get_children():
            if child.kind == CursorKind.PARM_DECL:
                parameters.append(child.spelling)
            elif child.kind == CursorKind.COMPOUND_STMT:
                statement = Block.from_node(child)
                
        mutation = ET.Element("mutation")
        for parameter in parameters:
            ET.SubElement(mutation, "arg", name=parameter)

        if node.type.spelling == 'void': 
            return Block('procedures_defnoreturn', mutation, node.spelling, statement)
        else: 
            return Block('procedures_defreturn', mutation, node.spelling, statement)
        
    def build_return_stmt(node):
        child = list(node.get_children())[0]
        return_val = Block.from_node(child)
        true_block = Block('logic_boolean', 'TRUE')
        return Block('procedures_ifreturn', true_block, return_val)

    def build_compound_stmt(node):
        """Creates block from compound statement node. 
        
        Each child node is converted to a block and stacked together. Returns the  
        top block, with top.stack_bottom set to the bottom block."""
        top = None
        bottom = None

        for child in node.get_children():
            new_block = Block.from_node(child)
            if top is None: top = new_block
            bottom = bottom.attach(new_block) if bottom is not None else new_block.stack_bottom
        
        if top is not None:
            top.stack_bottom = bottom
        return top

    def build_null_stmt(node):
        """
        Returns None.
        """
        return None

    def build_paren_expr(node):
        """Creates block from paranthesis expression node.
        
        Returns first child of node as block."""
        child = list(node.get_children())[0]
        return Block.from_node(child)

    def build_expression(node):
        """Creates block from expression node"""
        block_type = None
        args = []
        children = list(node.get_children())

        # get method spelling
        first_child = children[0]
        tokens = list(first_child.get_tokens())
        if first_child.kind == CursorKind.MEMBER_REF_EXPR:
            method_name = tokens[2].spelling
        elif first_child.kind == CursorKind.UNEXPOSED_EXPR:
            method_name = tokens[0].spelling
        else:
            raise TypeError(f"Method name could not be found in node type {children[0].kind}")

        if not method_name:
            raise TypeError(f"Method name could not be found")

        if not Block.methods.get(method_name):
            raise ValueError(f"Method \"{method_name}\" could not be found in method_blocks.yaml.")
        
        # create and add args
        method_data = Block.methods.get(method_name)
        block_type = method_data['block_type']

        if 'dropdown' in method_data: args.append(method_data['dropdown'])
        print(f"Method called: {method_name}")

        for child in children[1:]:
            method_name = None
            args.append(Block.from_node(child))

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

    def build_compound_assignment_operator(node):
        pass

    def build_number_literal(node):
        """Creates block from integer or floating literal node.
        
        Decimal: returns math_number block
        Binary: returns math_binary block
        Hexadecimal: returns math_hex block
        Octal: converts to decimal, throws a warning, and returns math_number block
        """
        tokens = list(node.get_tokens())
        spelling = tokens[0].spelling
        block_type = 'math_number'
        if spelling.lower().startswith("0x"): 
            block_type = 'math_hex'
            spelling = spelling[2:]
        elif spelling.lower().startswith("0b"): 
            block_type = 'math_binary'
            spelling = spelling[2:]
        elif spelling.startswith('0') and spelling != '0': 
            octal = spelling
            spelling = str(int(octal, 8))
            print(f"WARNING: Octal value {octal} converted to decimal value {spelling}")
        return Block(block_type, spelling)

    def build_while_stmt(node):
        """Creates block from while statement node"""
        children = [Block.from_node(child) for child in node.get_children()]
        return Block('controls_whileUntil', 'WHILE', children[0], children[1])
    
    def build_for_stmt(node):
        """Creates block from for statement node. 
        
        C syntax format is hard-coded to fit RoboBlocky limitations."""
        children = list(node.get_children())
        if len(children) < 4: raise ValueError(f"RoboBlocky for loops require 3 expressions but {len(children) - 1} were found.")

        init_node, cond_node, inc_node = children[0], children[1], children[2]
        var_name = from_block = to_block = by_block = None

        # initilization
        if init_node.kind == CursorKind.DECL_STMT:
            var_decl_node = list(init_node.get_children())[0]
            init_value_node = list(var_decl_node.get_children())[0]
            var_name = var_decl_node.spelling
            from_block = Block.from_node(init_value_node)
        elif init_node.kind == CursorKind.BINARY_OPERATOR and init_node.spelling == '=':
            init_children = list(init_node.get_children())
            var_name = init_children[0].spelling
            from_block = Block.from_node(init_children[1])
        else:
            raise ValueError("RoboBlocky for loop 1st statement only supports variable initialization (e.g. `j = 4`, `int i = 0`).")
        
        # conditional
        # TODO: adjustments for < vs <= and etc
        if cond_node.kind == CursorKind.BINARY_OPERATOR and cond_node.spelling in ['>', '>=', '<', '<=']:
            cond_children = list(cond_node.get_children())
            if cond_children[0].kind == CursorKind.UNEXPOSED_EXPR and cond_children[0].spelling == var_name:
                to_block = Block.from_node(cond_children[1])
            elif cond_children[1].kind == CursorKind.UNEXPOSED_EXPR and cond_children[1].spelling == var_name:
                to_block = Block.from_node(cond_children[0])
            else:
                raise ValueError(f"RoboBlocky requires initialized variable {var_name} to be present in for loop conditional.")
        else:
            raise ValueError("RoboBlocky for loop 2nd statement only supports comparison operators '>', '>=', '<', and '<='.")

        # increment
        if inc_node.kind == CursorKind.UNARY_OPERATOR:
            operator = list(inc_node.get_tokens())[1]
            if not (operator.spelling == '++' or operator.spelling == '--'):
                raise ValueError("RoboBlocky for loop 3rd statement only supports variable incrementing/decrementing.")
            child = list(inc_node.get_children())[0]
            if child.spelling != var_name:
                raise ValueError(f"RoboBlocky requires initialized variable {var_name} to be present in for loop increment.")
            
            by_block = Block('math_number', '1')
        elif inc_node.kind == CursorKind.COMPOUND_ASSIGNMENT_OPERATOR and inc_node.spelling in ['+=', '-=']:
            inc_children = list(inc_node.get_children())
            if inc_children[0].spelling != var_name:
                raise ValueError(f"RoboBlocky requires initialized variable {var_name} to be present in for loop increment.")
            
            by_block = Block.from_node(inc_children[1])
        else:
            raise ValueError("RoboBlocky for loop 3rd statement only supports variable incrementing/decrementing.")

        do_block = Block.from_node(children[3])
        return Block('controls_for', var_name, from_block, to_block, by_block, do_block)

    def build_if_stmt(node): 
        """
        Creates block from if statement node.
        
        Special case with non-fixed field and value count. Iterates though node to calculate
        number of elseif and else statements needed in mutation XML element. 

        Example args for 3 else ifs and 1 else:
        [mutation, condition0, compound0, condition1, compound1, condition2, compound2, compound3]
        """
        counts = {'elseif': 0, 'else': 0}
        args = []
        Block.recursive_build_if_stmt(node, counts, args)
        mutation = ET.Element("mutation", {"elseif": str(counts['elseif']), "else": str(counts['else'])})
        return Block('controls_if', mutation, *args)

    def recursive_build_if_stmt(node, counts, args):
        """
        Recursively creates blocks from children of if statement node. Keeps track of elseif and 
        else statements needed. Appends conditional block, compound block, and else if or else blocks. 
        """
        children = list(node.get_children())
        conditional, compound_stmt = children[0], children[1]
        args.append(Block.from_node(conditional))
        args.append(Block.from_node(compound_stmt))

        # recursively builds additional else/elseif statements
        if len(children) == 2: return
        if children[2].kind == CursorKind.IF_STMT:
            counts['elseif'] += 1
            Block.recursive_build_if_stmt(children[2], counts, args)
        else: 
            counts['else'] = 1
            args.append(Block.from_node(children[2]))

    def create_if_info(mutation):
        """
        Creates block_info dict for if block arguments from mutation XML element. 
        """
        block_info = { '_' : "mutation", 'IF0': 'value', 'DO0': 'statement'}
        else_if_count = int(mutation.get("elseif"))
        else_count = int(mutation.get("else"))
        for i in range(else_if_count):
            block_info[f'IF{i+1}'] = 'value'
            block_info[f'DO{i+1}'] = 'statement'
        if (else_count > 0):
            block_info['ELSE'] = 'statement'
        return block_info

    def build_decl_ref_expr(node):
        """
        Creates variable reference block from declare reference expression node. 

        Due to RoboBlocky limitations, only references to variables and parameters 
        are supported - otherwise an error will be thrown. 
        """
        referenced = node.referenced
        if referenced.kind == CursorKind.VAR_DECL or referenced.kind == CursorKind.PARM_DECL:
            return Block('variables_get', referenced.spelling)
        else:
            raise NotImplementedError(f"Declaration to {referenced.kind} is not supported.")

    def build_unexposed_expr(node):
        child = list(node.get_children())[0]
        return Block.from_node(child)

    def build_var_decl(node):
        """Creates block from variable declaration node.
        
        If no initialization, block type will be variables_create_with_type. Otherwise with initialization,
        block type will be variables_set_with_type. 
        """
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
if __name__ == "__main__":
    index = Index.create()
    tu = index.parse(c_file_path)
    root = from_tu(tu.cursor)

    xml_tree = ET.ElementTree(root)
    ET.indent(xml_tree, space='  ', level=0)
    xml_tree.write(f'{save_path}/convert.xml', encoding='utf-8')
    print(f"XML file generated.")