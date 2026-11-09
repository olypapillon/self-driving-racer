# Build Your Own Racer (learning path)

This is the step-by-step plan the game in this repository was built from. The goal is to learn by
building each part yourself, starting with a moving rectangle and eventually
reaching a Mario Kart-style pseudo-3D racer.

Do the stages in order. Do not move on until the current stage works and you can
explain what every line does.

## 1. Set up Python and Pygame

Create a virtual environment so this project's packages stay separate from your
other Python projects:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install pygame-ce
```

Recommended reading:

- [Python virtual environments](https://docs.python.org/3/tutorial/venv.html)
- [Pygame-ce quick start](https://pyga.me/docs/)
- [Python tutorial](https://docs.python.org/3/tutorial/index.html) if you need a
  refresher on functions, modules, or classes

## 2. Open a Window

Create `src/main.py`. Using the Pygame-ce quick start as a reference, make it:

- initialize Pygame;
- open an 800 by 600 window;
- process the quit event;
- fill the screen with one color every frame;
- update the display;
- limit the loop to 60 frames per second; and
- call `pygame.quit()` after the loop.

You are finished when the window stays responsive and closes normally.

Learn about:

- [the Pygame-ce quick-start game loop](https://pyga.me/docs/)
- [events](https://pyga.me/docs/ref/event.html)
- [`Clock` and frame timing](https://pyga.me/docs/ref/time.html)

## 3. Make a Rectangle Move

Draw a rectangle to represent your car. Store its position separately from the
rectangle used to draw it. Read held keys every frame and use WASD or the arrow
keys to move it.

Make movement frame-rate independent:

1. Get elapsed milliseconds from `Clock.tick(60)`.
2. Divide by 1000 to get seconds.
3. Multiply movement speed by those elapsed seconds.

You are finished when movement feels the same at different frame-rate limits and
the car cannot leave the window.

Learn about:

- [moving an image](https://www.pygame.org/docs/tut/MoveIt.html)
- [keyboard state](https://pyga.me/docs/ref/key.html)
- [drawing shapes](https://pyga.me/docs/ref/draw.html)
- [`Rect` and `FRect`](https://pyga.me/docs/ref/rect.html)

Experiments:

- Try 100, 300, and 600 pixels per second.
- Temporarily change the frame limit to 30 and then 144.
- Print the position once per second rather than every frame.

## 4. Turn Movement into Car Handling

Replace direct four-direction movement with these values:

- position;
- direction or heading;
- current speed;
- acceleration;
- braking strength;
- friction or drag;
- maximum forward speed; and
- maximum reverse speed.

Up should increase speed, down should brake and eventually reverse, and left or
right should change the heading. Move the car forward along its heading. Start
with a triangle or rectangle; artwork can wait.

You are finished when the car accelerates gradually, coasts to a stop, reverses,
and only turns effectively while moving.

Learn about:

- [`Vector2`](https://pyga.me/docs/ref/math.html)
- [rotating a surface](https://pyga.me/docs/ref/transform.html)
- [Python classes](https://docs.python.org/3/tutorial/classes.html) when you are
  ready to place the car's related state and behavior together

Experiments:

- Change acceleration without changing maximum speed.
- Make steering depend on the percentage of maximum speed.
- Reverse the steering direction while the car is moving backward.

## 5. Build a Top-Down Track

Start with an oval or a wide loop. Primitive shapes are enough. Give the road and
grass different colors, then decide whether the car is on the road.

When the car reaches grass:

- lower its maximum speed;
- add stronger drag; and
- keep steering available so returning to the road is possible.

Next, add a finish line and several ordered checkpoints. Award a lap only after
the car passes all checkpoints in order and crosses the finish line going the
correct direction. This prevents reversing over the line to gain laps.

You are finished when you can complete a valid three-lap race with a timer and
restart it without relaunching the program.

Useful references:

- [Pygame drawing functions](https://pyga.me/docs/ref/draw.html)
- [rectangle collision tools](https://pyga.me/docs/ref/rect.html)
- [sprite concepts](https://pyga.me/docs/ref/sprite.html)
- [Pygame newbie guide](https://www.pygame.org/docs/tut/newbieguide.html)

## 6. Separate the Driver from the Car

Before adding AI, make the car update from three input values rather than reading
the keyboard inside the car code:

- throttle from 0 to 1;
- brake from 0 to 1; and
- steering from -1 to 1.

The keyboard creates those values, while the car only consumes them. Later, an
AI can produce the same three values without changing the vehicle physics.

You are finished when removing the keyboard code does not require changing the
car's update logic.

## 7. Study Pseudo-3D Roads

Only start this after the top-down race works. Pseudo-3D adds projection math and
is much easier when the driving and race rules are already understood.

Read these in order:

1. [Lou's Pseudo-3D Road page](https://www.extentofthejam.com/pseudo/) explains
   road segments, projection, curves, hills, and drawing order.
2. [Jake Gordon: straight roads](https://jakesgordon.com/writing/javascript-racer-v1-straight/)
   builds the projection gradually.
3. Continue with [curves](https://jakesgordon.com/writing/javascript-racer-v2-curves/),
   [hills](https://jakesgordon.com/writing/javascript-racer-v3-hills/), and
   [the finished racer](https://jakesgordon.com/writing/javascript-racer-v4-final/).

Those examples use JavaScript, but the important parts are the math and data
model. Reimplement the ideas in Python rather than translating line by line.

Suggested progression:

1. Draw one straight road from horizontal segments.
2. Make the segments move toward the camera.
3. Loop the road.
4. Add left and right player offset.
5. Add gentle curves.
6. Add hills.
7. Reconnect your timer, laps, and grass slowdown.

## 8. Add Self-Driving Later

Begin with waypoint following, not machine learning. Give the AI a target point
ahead on the track and calculate whether that target lies left or right of the
car. Convert the result into steering, and reduce throttle for sharp turns.

Once that works, useful next topics are:

- steering behaviors;
- ray or distance sensors;
- path planning; and
- reinforcement learning.

Keep the hand-written controller as a baseline so you can tell whether a more
advanced method is actually improving the racer.

## A Good Learning Routine

- Build one visible change at a time.
- Run the program after every small change.
- When an error occurs, read the final traceback line first.
- Change constants and predict the result before running again.
- Recreate tutorial examples from memory after you understand them.
- Save working milestones before beginning the next stage.
- Ask for explanations or hints before asking for complete code.

Your first goal is only Stage 2: an empty, responsive Pygame window. Everything
else can wait until that works.
