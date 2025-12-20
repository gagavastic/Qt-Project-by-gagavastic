extends Area2D
@onready var player = $seal
var direction = (player.global_position - global_position).normalized()
func ddd():
		
		rotation = direction.angle()
func gfjlgkf():
			position += direction * 10 
