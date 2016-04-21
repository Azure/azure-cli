from .generated import command_table as generated_command_table
from .custom import command_table as convenience_command_table

command_table = generated_command_table
command_table.update(convenience_command_table)
