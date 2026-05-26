class_name Guest
extends Resource
## A guest waiting to be served.

enum GuestType { REGULAR, BUSINESS, VIP, CRITIC }

@export var guest_type: GuestType = GuestType.REGULAR
@export var budget: float = 40.0
@export var patience_ticks: int = 5
@export var expectation: float = 3.0
@export var wait_timer: int = 0
@export var mood: float = 1.0

## String key into GameConfig.guest_types()
func type_key() -> String:
	match guest_type:
		GuestType.REGULAR:  return "regular"
		GuestType.BUSINESS: return "business"
		GuestType.VIP:      return "vip"
		GuestType.CRITIC:   return "critic"
	return "regular"

func type_label() -> String:
	return GameConfig.guest_types()[type_key()]["label"]

func priority() -> int:
	return GameConfig.guest_types()[type_key()]["priority"]