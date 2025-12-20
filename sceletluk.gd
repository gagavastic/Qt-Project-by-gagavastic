extends CharacterBody2D

const SPEED = 300.0
const JUMP_VELOCITY = -246.0
var gravity = ProjectSettings.get_setting("physics/2d/default_gravity") or 980.0
var hp = 10
var damage = 10
var is_chasing = false 
var direction = Vector2.ZERO 
@onready var player = $"../seal"
@onready var anim = $AnimatedSprite2D
var can_attack = false
@onready var timer = $Timer
var atacuu = false
var ghgh = false
var is_attacking = false 

func _physics_process(_delta: float) -> void:
	if not player:
		return
	
	# Гравитация
	if not is_on_floor():
		velocity.y += 10
	else:
		if is_chasing and player.position.y < position.y and not is_attacking:
			jump()

	direction = (player.position - position).normalized()
	

	if is_chasing:
		velocity.x = direction.x * SPEED
	else:
		velocity.x = 0

	if is_attacking:
		pass
	elif is_chasing:
		anim.play("run")
	else:
		anim.play("default")

	move_and_slide()
	
	# Поворот спрайта
	update_sprite_direction()

func update_sprite_direction():
	if direction.x < 0:
		anim.flip_h = true
	elif direction.x > 0:
		anim.flip_h = false

func _on_area_2d_body_entered(body: Node2D) -> void:
	if body == player:
		is_chasing = true

func jump():
	velocity.y = JUMP_VELOCITY

func sceletbol():
	if can_attack:
		hp -= 1
		queue_free()
		print("attacka прошла успешно")

func sceletdeath():
	queue_free()
	
func fhdf():
	if hp <= 0:
		sceletdeath()
		print("враг поежден")

func attakuu(_a):
	if atacuu and player:
		print(player.hp)
		player.hp -= 1
		if player.hp <= 0:
			sealleave()  

func _on_area_2d_2_body_entered(_body: Node2D) -> void:
	if _body == player:
		ghgh = true
		atacuu = true
		is_attacking = true  
		anim.play("ataka")  
		print("фаааааааааа")
		timer.start()

func _on_area_2d_2_body_exited(_body: Node2D) -> void:
	if _body == player:
		atacuu = false
		ghgh = false
		is_attacking = false 
		timer.stop()
		print("сольььььььь")

func _on_timer_timeout() -> void:
	attakuu(player)

func _on_animated_sprite_2d_animation_finished():
	if anim.animation == "attack":
		is_attacking = false 

func sealleave():
	if player:
		player.queue_free()
		
		
func take_damage(a):
	hp -= a
	queue_free()


func _on_area_2d_body_exited(_body: Node2D) -> void:
	pass # Replace with function body.

func dfd():
	if hp <= 0:
		queue_free()
