extends Spatial

const chunk_size = 64
const chunks_amount = 16

var noise
var chunks = {}
var unready_chunks = {}
var thread

func _ready():
	randomize()
	noise = OpenSimplexNoise.new()
	noise.seed = randi()
	noise.octaves = 6
	noise.period = 80
	
	thread = Thread.new()
	
func add_chunk(x, z):
	var key = str(x)  + "," + str(z)
	if chunks.has(key) or unready_chunks.has(key):
		return
	
	if not thread.is_active():
		thread.start(self, "load_chunk", [thread, x, z])
		unready_chunks[key] = 1
		
func load_chunk(array):
	var thread = array[0]
	var x = array[1]
	var z = array[2]
	
	var chunk = Chunk.new(noise, x * chunk_size, z * chunk_size, chunk_size)
	chunk.translation = Vector3(x * chunk_size, 0, z * chunk_size)
	
	call_deferred("load_done", chunk, thread)
	
func load_done(chunk, thread):
	add_child(chunk)
	var key = str(chunk.x / chunk_size) + "," + str(chunk.z / chunk_size)
	chunks[key] = chunk
	unready_chunks.erase(key)
	thread.wait_to_finish()
	
func get_chunk(x, z):
	var key = str(x)  + "," + str(z)
	if chunks.has(key):
		return chunks.get(key)
	return null
	
func _process(delta):
	update_chunks()
	clean_up_chunks()
	reset_chunks()
	
func update_chunks():
	var camera_translation = $Camera.translation
	var c_x = int(camera_translation.x) / chunk_size
	var c_z = int(camera_translation.z) / chunk_size
	
	for x in range(c_x - chunks_amount * 0.5, c_x + chunks_amount * 0.5):
		for z in range(c_z - chunks_amount * 0.5, c_z + chunks_amount * 0.5):
			add_chunk(x, z)
			var chunk = get_chunk(x, z)
			if chunk != null:
				chunk.should_remove = false
	
func clean_up_chunks():
	for key in chunks:
		var chunk = chunks[key]
		if chunk.should_remove:
			chunk.queue_free()
			chunks.erase(key)
	
func reset_chunks():
	for key in chunks:
		chunks[key].should_remove = true