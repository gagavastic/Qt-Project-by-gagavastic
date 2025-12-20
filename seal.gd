extends CharacterBody2D

@onready var seal = $"."
var damage = 1
var hp = 50

@onready var anim = $CollisionShape2D/AnimatedSprite2D
const SPEED = 500.0
const JUMP_VELOCITY = -800.0
var gravity = ProjectSettings.get_setting("physics/2d/default_gravity")
var ddd = false
@onready var timer = $Timer2
var vargy = []   # для атаки вверх
var vargy2 = []  # для атаки вниз
var vargy3 = []  # для атаки влево
var can_attack = true
var current_attack = "none"  # текущее направление атаки
var vargy4 = []
var is_attacking = false  # Добавляем флаг атаки
var v = false

func _physics_process(delta: float) -> void:
	velocity.y += gravity * delta
	
	# Обработка прыжка
	if Input.is_action_just_pressed("ui_accept") and is_on_floor():
		velocity.y = JUMP_VELOCITY
	
	# Обработка направления атаки
	if Input.is_action_just_pressed("ui_accept"):
		current_attack = "up"
		v = false
	elif Input.is_action_just_pressed("ui_down") and is_on_floor():
		current_attack = "down"
		v = true
	elif Input.is_action_just_pressed("ui_left"):
		current_attack = "left"
		v=false
	elif Input.is_action_just_pressed("ui_right"):
		current_attack = "right"
		v=false
	
	# Обработка атаки
	if Input.is_action_just_pressed("a") and can_attack:
		perform_attack()
	
	var direction = Input.get_axis("ui_left", "ui_right")
	if direction:
		velocity.x = direction * SPEED
	else:
		velocity.x = move_toward(velocity.x, 0, SPEED)

	update_animations(direction)
	move_and_slide()
	dfdfasdfa()
	dddddd()
func update_animations(direction):
	# Если идет атака, не меняем анимацию
	if is_attacking:
		return
	
	if direction == -1:
		anim.flip_h = true
	elif direction == 1:
		anim.flip_h = false
	
	if not is_on_floor():
		if velocity.y < 0:
			anim.play("jump")
		else:
			anim.play("fall")
	else:
		if direction != 0:
			anim.play("run")
		else:
			anim.play("default")

func perform_attack():
	if not can_attack:
		return
	
	can_attack = false
	is_attacking = true  # Устанавливаем флаг атаки
	
	# Проверяем направление атаки
	if current_attack == "up":
		anim.play("fishatak")
	elif current_attack == "down":
		anim.play("fishatak")
	elif current_attack == "right":
		anim.play("ataka")
	elif current_attack == "left":
		anim.play("ataka")
	elif current_attack == "down" and "right":
		anim.play("fishatak")
	elif current_attack == "down" and "left":
		anim.play("fishatak")
	else:
		anim.play("ataka")
		# Настраиваем переворот спрайта
		if current_attack == "up":
			anim.flip_v = true  # Переворачиваем спрайт для атаки вверх
		else:
			anim.flip_v = false  # Сбрасываем переворот для атаки вниз

		
		# Настраиваем горизонтальный переворот для атаки влево/вправо
		if current_attack == "left":
			anim.flip_h = true
		elif current_attack == "right":
			anim.flip_h = false
	
	# Атакуем врагов в соответствующей зоне
	match current_attack:
		"up":
			attack_enemies(vargy)
		"down":
			attack_enemies(vargy2)
		"left":
			attack_enemies(vargy3)
		"right":
			attack_enemies(vargy4)
		_:
			# Атака по умолчанию (если не указано направление)
			attack_enemies(vargy2)
	
	timer.start()

func attack_enemies(enemy_list):
	for i in range(enemy_list.size() - 1, -1, -1):
		var enemy = enemy_list[i]
		if is_instance_valid(enemy) and "hp" in enemy:
			enemy.hp -= damage
			print("Нанесен урон врагу, осталось HP: ", enemy.hp)
			
			if enemy.hp <= 0:
				enemy.queue_free()
				enemy_list.remove_at(i)
		elif not is_instance_valid(enemy):
			enemy_list.remove_at(i)

func _on_area_2d_4_body_entered(body: Node2D) -> void:
	if body != seal and body.has_method("take_damage"):
		if not vargy.has(body):
			vargy.append(body)
			print("Враг добавлен в зону атаки вверх")

func _on_area_2d_4_body_exited(body: Node2D) -> void:
	if vargy.has(body):
		vargy.erase(body)
		print("Враг удален из зоны атаки вверх")

func _on_area_2d_3_body_entered(body: Node2D) -> void:
	if body != seal and body.has_method("take_damage"):
		if not vargy2.has(body):
			vargy2.append(body)
			print("Враг добавлен в зону атаки вниз")

func _on_area_2d_3_body_exited(body: Node2D) -> void:
	if vargy2.has(body):
		vargy2.erase(body)

func _on_area_2d_2_body_entered(body: Node2D) -> void:
	if body != seal and body.has_method("take_damage"):
		if not vargy3.has(body):
			vargy3.append(body)
			print("Враг добавлен в зону атаки влево")

func _on_area_2d_2_body_exited(body: Node2D) -> void:
	if vargy3.has(body):
		vargy3.erase(body)

func _on_timer_2_timeout() -> void:
	can_attack = true
	is_attacking = false  # Сбрасываем флаг атаки
	anim.flip_v = false  # Сбрасываем вертикальный переворот


func _on_area_2d_body_entered(body: Node2D) -> void:
	if body != seal and body.has_method("take_damage"):
		if not vargy4.has(body):
			vargy4.append(body)
			print("Враг добавлен в зону атаки вправо")


func _on_area_2d_body_exited(body: Node2D) -> void:
	if vargy4.has(body):
		vargy4.erase(body)

func dfdfasdfa():
	if Input.is_action_just_pressed("a"):
		if Input.is_action_just_pressed("ui_down"):
			anim.play("fishatak")
			

func dddddd():
	if v:
		if Input.is_action_just_pressed("a"):
			anim.play("fishatak")

func rivok():
	if current_attack == "ui_left":
		if Input.is_action_just_pressed("v"):
			velocity.x += 1000
	elif current_attack == "right":
		if Input.is_action_just_pressed("v"):
			velocity.x -= 1000
