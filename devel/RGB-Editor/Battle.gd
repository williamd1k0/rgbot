tool
extends Control

export(bool) var print_info = false setget _set_print_info

func _set_print_info(b):
	if b: call_deferred('print_info')

func print_info():
	print_grounds()
	print_roosters()

func print_grounds():
	var tmp = """Grounds:
{
    LEFT: %s,
    RIGHT: %s,
}"""
	var l = $Grounds/Left.rect_global_position
	var r = $Grounds/Right.rect_global_position
	print(tmp % [l, r])

func print_roosters():
	var tmp = """Roosters:
{
    LEFT: %s,
    RIGHT: %s,
}
"""
	var l = Rect2($Roosters/A.rect_global_position, $Roosters/A.rect_size)
	var r = Rect2($Roosters/B.rect_global_position, $Roosters/B.rect_size)
	print(tmp % [l, r])
