extends Area2D

func d():
	if Input.is_action_just_pressed("ui_accept"):
		velocity.x +=10
