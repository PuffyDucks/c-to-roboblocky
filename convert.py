# ADD:
# fix math blocks with mutations
## arrays
# lists
# results
# prompts
# ? altho im not sure if ? even works in roboblocky
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
    declared_functions = {}

    def __init__(self, block_type: str, *args):
        '''
        Build block from str block_type and *args. *args is list of strings for fields and blocks for values.
        '''
        block_info = Block.args.get(block_type)

        # block_info modifications with mutations 
        if block_type == 'controls_if':
            block_info = Block.create_if_info(args[0])
        elif block_type == 'procedures_callreturn':
            block_info = Block.create_func_info(args[0])
        elif block_type == 'array_create_type':
            block_info = Block.create_array_info(args[0])

        if not block_info:
            raise ValueError(f"Block type '{block_type}' could not be found in block_args.yaml.")
        if len(args) != len(block_info):
            raise TypeError(f"'{block_type}'() takes {len(block_info)} argument{'s' if len(block_info) > 1 else ''}, but recieved {len(args)}.")

        # create xml element of type 'block'
        super().__init__('block', type=block_type)
        self.stack_bottom = self
        
        # add args to xml element from block_info and args
        for (arg_name, arg_type), arg_value in zip(block_info.items(), args):
            if arg_type == 'mutation': 
                self.append(arg_value)
                continue
            
            arg_element = ET.SubElement(self, arg_type, name=arg_name)
            if arg_type == 'field':
                # ensure arg_vaule is not non-string block. extract text if string block
                if isinstance(arg_value, ET.Element):
                    string_value = arg_value.find(".//field[@name='TEXT']")
                    if string_value is not None: arg_value = string_value.text
                    else: raise TypeError(f"Non-string block was passed into argument {arg_name} for block {block_type}.")
                arg_element.text = str(arg_value)
            elif arg_value is not None:
                # ensure arg_vaule is block
                if not isinstance(arg_value, ET.Element): raise TypeError(f"Block was not passed into argument {arg_name} for block {block_type}.")
                arg_element.append(arg_value)
    
    @staticmethod
    def from_node(node):
        '''
        Builds and returns block from ast node.
        '''
        print(f'{node.kind} {node.spelling}')
        cursor_kind_map = {
            CursorKind.FUNCTION_DECL: Block.build_function_decl,
            CursorKind.RETURN_STMT: Block.build_return_stmt,
            
            CursorKind.COMPOUND_STMT: Block.build_compound_stmt,
            CursorKind.NULL_STMT: Block.build_null_stmt,
            CursorKind.PAREN_EXPR: Block.build_paren_expr,
            CursorKind.CALL_EXPR: Block.build_call_expr,
            CursorKind.DECL_REF_EXPR: Block.build_decl_ref_expr,
            CursorKind.UNEXPOSED_EXPR: Block.build_unexposed_expr,
            CursorKind.INIT_LIST_EXPR: Block.create_init_list_expr,

            CursorKind.DECL_STMT: Block.build_decl_stmt,

            CursorKind.INTEGER_LITERAL: Block.build_number_literal,
            CursorKind.FLOATING_LITERAL: Block.build_number_literal,
            CursorKind.STRING_LITERAL: Block.build_string_literal,
            CursorKind.UNARY_OPERATOR: Block.build_unary_operator,
            CursorKind.BINARY_OPERATOR: Block.build_binary_operator,
            CursorKind.COMPOUND_ASSIGNMENT_OPERATOR: Block.build_compound_assignment_operator,

            CursorKind.WHILE_STMT: Block.build_while_stmt,
            CursorKind.FOR_STMT: Block.build_for_stmt,
            CursorKind.IF_STMT: Block.build_if_stmt
        }

        if cursor_kind_map.get(node.kind):
            return cursor_kind_map.get(node.kind)(node)
                    
        raise NotImplementedError(f"Node type {node.kind} is not supported.")

    def build_function_decl(node):
        '''
        Creates block from function declaration node. 
        
        If function is main, returns only the blocks from the compound statement 
        are returned. Otherwise, the blocks are returned as a function block. 

        Non-main functions are added to the `declared_functions` static dictionary,
        as a name:args pair.
        '''
        func_name = node.spelling
        # Generate the main function without a function block 
        if func_name == 'main':
            main_stack = Block('text_comment', "Generated with Luna\'s C-to-RoboBlocky transpiler v0.5")        
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

        Block.declared_functions[func_name] = parameters
        if node.type.spelling == 'void': 
            return Block('procedures_defnoreturn', mutation, func_name, statement)
        else: 
            return Block('procedures_defreturn', mutation, func_name, statement)
        
    def build_return_stmt(node):
        child = list(node.get_children())[0]
        return_val = Block.from_node(child)
        true_block = Block('logic_boolean', 'TRUE')
        return Block('procedures_ifreturn', true_block, return_val)

    def build_compound_stmt(node):
        '''
        Creates block from compound statement node. 
        
        Each child node is converted to a block and stacked together. Returns the  
        top block, with top.stack_bottom set to the bottom block.
        '''
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
        '''
        Returns None.
        '''
        return None

    def build_paren_expr(node):
        '''
        Creates block from paranthesis expression node.
        
        Returns first child of node as block.
        '''
        child = list(node.get_children())[0]
        return Block.from_node(child)

    def build_call_expr(node):
        '''
        Creates block from expression node
        '''
        block_type = None
        method_name = None
        args = []
        children = list(node.get_children())

        # get method spelling
        first_child = children[0]
        tokens = list(first_child.get_tokens())
        if first_child.kind == CursorKind.UNEXPOSED_EXPR:
            method_name = tokens[0].spelling
        elif first_child.kind == CursorKind.MEMBER_REF_EXPR:
            # For RoboBlocky methods that use a class
            method_name = tokens[2].spelling
        else:
            raise TypeError(f"Method name could not be found in node type {children[0].kind}.")
        
        if Block.methods.get(method_name):
            # Method built into RoboBlocky
            method_data = Block.methods.get(method_name)
            block_type = method_data['block_type']
            if 'dropdown' in method_data: args.append(method_data['dropdown'])
            print(f"RoboBlocky method called: {method_name}")
        elif Block.declared_functions.get(method_name):
            # Calling user defined function
            block_type = 'procedures_callreturn'
            # mutation block listing function args
            mutation = ET.Element("mutation", name=method_name)
            for function_arg in Block.declared_functions[method_name]:
                ET.SubElement(mutation, "arg", name=function_arg)
            args.append(mutation)
        else:
            raise ValueError(f"Could not find method or function {method_name}().")

        isColorBlock = block_type in ['draw_background_color', 'draw_stroke_color', 'draw_fill']
        # create and add args
        for child in children[1:]:
            # special case for color blocks
            if isColorBlock and child.kind == CursorKind.STRING_LITERAL: 
                args.append(Block.build_color_block(child))
            else: args.append(Block.from_node(child))

        return Block(block_type, *args)

    def create_func_info(mutation):
        '''
        Creates block_info dict for function call block arguments from 
        mutation XML element. 
        '''
        block_info = { '_' : "mutation"}
        for i in range(len(mutation)):
            block_info[f'ARG{i}'] = 'value'
        return block_info

    def build_unary_operator(node):
        tokens = list(node.get_tokens())
        operator = tokens[0].spelling
        child = list(node.get_children())[0]

        if operator not in ['!', '-', '++', '--']:
            # check 2nd token 
            if tokens[1].spelling in ['++', '--']: 
                operator = tokens[1].spelling
            else: 
                raise NotImplementedError(f"Unary operator {operator} is not supported.")

        if operator == '!':
            return Block('logic_negate', Block.from_node(child))
        elif operator == '-':
            return Block('math_negative', Block.from_node(child))
        
        var_name = child.spelling
        var_block = Block('variables_get', var_name)
        int_block = Block('math_number', 1)
        if operator == '++': 
            operation_block = Block('math_arithmetic', 'ADD', var_block, int_block) 
        elif operator == '--': 
            operation_block = Block('math_arithmetic', 'MINUS', var_block, int_block) 
        return Block('variables_set', var_name, operation_block)

    def build_binary_operator(node):
        '''
        Creates block from binary operator node
        '''
        arithmetic_map = {'+': 'ADD', '-': 'MINUS', '*': 'MULTIPLY', '/': 'DIVIDE'}
        comparison_map = {'==': 'EQ', '!=': 'NEQ', '<': 'LT', '<=': 'LTE', '>': 'GT', '>=': 'GTE'}
        logical_map = {'&&': 'AND', '||': 'OR'}
        operator = node.spelling

        # variable assignment
        if operator == '=':
            children = list(node.get_children())
            return Block('variables_set', children[0].spelling, Block.from_node(children[1]))

        operands = [Block.from_node(operand) for operand in node.get_children()]
        if operator == '%':
            return Block('math_modulo', operands[0], operands[1])
        if operator in arithmetic_map:
            return Block('math_arithmetic', arithmetic_map[operator], operands[0], operands[1])
        elif operator in comparison_map:
            return Block('logic_compare', comparison_map[operator], operands[0], operands[1])
        elif operator in logical_map:
            return Block('logic_operation', logical_map[operator], operands[0], operands[1])
        raise ValueError(f"Binary operator {operator} is not supported.")

    def build_compound_assignment_operator(node):
        '''
        Creates block from compound assignment operator node.

        Throws an error for bitwise operators.
        '''
        operator = node.spelling[0]

        arithmetic_map = {'+': 'ADD', '-': 'MINUS', '*': 'MULTIPLY', '/': 'DIVIDE'}
        if operator not in arithmetic_map and operator != '%':
            raise ValueError(f"Bitwise compound assignment operator {operator} is not supported.")
        
        operands = [Block.from_node(operand) for operand in node.get_children()]
        if operator == '%':
            operation_block = Block('math_modulo', operands[0], operands[1])
        else: 
            operation_block = Block('math_arithmetic', arithmetic_map[operator], operands[0], operands[1])

        var_name = list(node.get_children())[0].spelling
        return Block('variables_set', var_name, operation_block)

    def build_number_literal(node):
        '''
        Creates block from integer or floating literal node.
        
        Decimal: returns math_number block
        Binary: returns math_binary block
        Hexadecimal: returns math_hex block
        Octal: converts to decimal, throws a warning, and returns math_number block
        '''
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
    
    def build_string_literal(node):
        '''
        Creates block string literal node.
        '''
        tokens = list(node.get_tokens())
        spelling = tokens[0].spelling.strip('"')
        return Block("text", spelling)

    def build_color_block(node):
        '''
        Creates color block from string literal node.
        '''
        named_colors = {"red": "#FF0000", "green": "#00FF00", "blue": "#0000FF", 
                        "cyan": "#00FFFF", "magenta": "#FF00FF", "yellow": "#FFFF00", 
                        "orange": "#FFA500", "brown": "#A52A2A", 
                        "white": "#FFFFFF", "black": "#000000"}
        
        color = node.spelling.strip('"')
        if color in named_colors:
            color = named_colors[color]
        return Block('colour_picker', color)

    def build_while_stmt(node):
        '''
        Creates block from while statement node
        '''
        children = [Block.from_node(child) for child in node.get_children()]
        return Block('controls_whileUntil', 'WHILE', children[0], children[1])
    
    def build_for_stmt(node):
        '''
        Creates block from for statement node. 
        
        C syntax format is hard-coded to fit RoboBlocky limitations.
        '''
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
        '''
        Creates block from if statement node.
        
        Special case with non-fixed field and value count. Iterates though node to calculate
        number of elseif and else statements needed in mutation XML element. 

        Example args for 3 else ifs and 1 else:
        [mutation, condition0, compound0, condition1, compound1, condition2, compound2, compound3]
        '''
        counts = {'elseif': 0, 'else': 0}
        args = []
        Block.recursive_build_if_stmt(node, counts, args)
        mutation = ET.Element("mutation", {"elseif": str(counts['elseif']), "else": str(counts['else'])})
        return Block('controls_if', mutation, *args)

    def recursive_build_if_stmt(node, counts, args):
        '''
        Recursively creates blocks from children of if statement node. Keeps track of elseif and 
        else statements needed. Appends conditional block, compound block, and else if or else blocks. 
        '''
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
        '''
        Creates block_info dict for if block arguments from mutation XML element. 
        '''
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
        '''
        Creates variable reference block from declare reference expression node. 

        Due to RoboBlocky limitations, only references to variables and parameters 
        are supported - otherwise an error will be thrown. 
        '''
        referenced = node.referenced
        if referenced.kind == CursorKind.VAR_DECL or referenced.kind == CursorKind.PARM_DECL:
            return Block('variables_get', referenced.spelling)
        else:
            raise NotImplementedError(f"Declaration to {referenced.kind} is not supported.")

    def build_unexposed_expr(node):
        child = list(node.get_children())[0]
        return Block.from_node(child)

    def build_var_decl(node):
        '''
        Creates block from variable declaration node.
        
        If no initialization, block type will be variables_create_with_type. Otherwise with initialization,
        block type will be variables_set_with_type. 
        '''
        var_type = node.type.spelling
        var_name = node.spelling
        children = list(node.get_children())
        child = children[0] if children else None
        isNotArray = not var_type.endswith(']')
        
        if isNotArray and child is None:
            # non array declare
            return Block('variables_create_with_type', var_type, var_name)
        elif isNotArray:
            # non array declare and initialize
            return Block('variables_set_with_type', var_type, var_name, Block.from_node(child))
        
        # var type is array
        def find_init_list(node):
            # condition to look for
            if node.kind == CursorKind.INIT_LIST_EXPR:
                return Block.from_node(node)
            # recursive search
            for child in node.get_children():
                init_blocks = find_init_list(child)
                if init_blocks is not None:
                    return init_blocks
            return None
        args = find_init_list(node)
        var_type = var_type.split("[")[0] 
        
        if args is None:
            # array declare 
            return Block('array_create_with_type', var_type, var_name, Block.from_node(child))
        else: 
            # array declare and initialize
            mutation = ET.Element("mutation", {"items": str(len(args))})
            return Block('array_create_type', mutation, var_type, var_name, *args)

    def create_init_list_expr(node):
        args = []
        for child in node.get_children():
            args.append(Block.from_node(child))
        return args

    def create_array_info(mutation):
        '''
        Creates block_info dict for array_create_type block arguments from mutation XML element. 
        '''
        block_info = { '_' : "mutation", "TYPE" : "field", "VAR" : "field"}
        element_count = int(mutation.get('items'))
        for i in range(element_count):
            block_info[f'ADD{i}'] = 'value'
        return block_info

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
        '''
        Appends child block wrapped in 'next' element. Returns bottom block.

        In RoboBlocky, attaches the child block directly below the parent block. 
        '''
        if child_block is None:
            return self

        element_next = ET.SubElement(self, 'next')
        element_next.append(child_block)
        return child_block.stack_bottom
    
def from_tu(node):
    '''
    Sets up root from tu cursor, and initiates building main function. 
    '''
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