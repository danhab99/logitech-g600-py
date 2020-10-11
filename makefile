install:
	pip3 install -r requirements.txt

	ratbagctl "Logitech Gaming Mouse G600" profile 0 button 5 action set macro KEY_P
	ratbagctl "Logitech Gaming Mouse G600" profile 0 button 6 action set macro KEY_N
	ratbagctl "Logitech Gaming Mouse G600" profile 0 button 7 action set macro KEY_M
	ratbagctl "Logitech Gaming Mouse G600" profile 0 button 8 action set macro KEY_A
	ratbagctl "Logitech Gaming Mouse G600" profile 0 button 9 action set macro KEY_B
	ratbagctl "Logitech Gaming Mouse G600" profile 0 button 10 action set macro KEY_C
	ratbagctl "Logitech Gaming Mouse G600" profile 0 button 11 action set macro KEY_D
	ratbagctl "Logitech Gaming Mouse G600" profile 0 button 12 action set macro KEY_E
	ratbagctl "Logitech Gaming Mouse G600" profile 0 button 13 action set macro KEY_F
	ratbagctl "Logitech Gaming Mouse G600" profile 0 button 14 action set macro KEY_G
	ratbagctl "Logitech Gaming Mouse G600" profile 0 button 15 action set macro KEY_H
	ratbagctl "Logitech Gaming Mouse G600" profile 0 button 16 action set macro KEY_I
	ratbagctl "Logitech Gaming Mouse G600" profile 0 button 17 action set macro KEY_J
	ratbagctl "Logitech Gaming Mouse G600" profile 0 button 18 action set macro KEY_K
	ratbagctl "Logitech Gaming Mouse G600" profile 0 button 19 action set macro KEY_L
	
	xinput disable $(xinput | grep -Po "(?<=Logitech Gaming Mouse G600 Keyboard).*" | grep -Po "(?<=id=)\d+")