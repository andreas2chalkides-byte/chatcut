import sys, time, bpy
sys.path.insert(0, "/home/user/chatcut/cgi")
import scene as S
S.reset()
S.build()
S.world_and_lights(haze=0.0)
S.camera((-0.55, -0.95, 0.42), (0.0, 0.0, 0.24), lens=40)
S.render_settings((1280, 720), 24)
bpy.context.scene.render.filepath = sys.argv[-1]
t = time.time()
bpy.ops.render.render(write_still=True)
print("RENDER_SECONDS", round(time.time() - t, 1))
