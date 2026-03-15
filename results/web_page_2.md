# Lorenz system - Wikipedia

URL: https://en.wikipedia.org/wiki/Lorenz_system
Relevance Score: 5.15

# Lorenz system

This article may be too technical for most readers to understand. (December 2023) |

The **Lorenz system** is a set of three ordinary differential equations, first developed by the meteorologist Edward Lorenz while studying atmospheric convection. It is a classic example of a system that can exhibit chaotic behavior, meaning its output can be highly sensitive to small changes in its starting conditions.

For certain values of its parameters, the system's solutions form a complex, looping pattern known as the **Lorenz attractor**. The shape of this attractor, when graphed, is famously said to resemble a butterfly. The system's extreme sensitivity to initial conditions gave rise to the popular concept of the butterfly effect—the idea that a small event, like the flap of a butterfly's wings, could ultimately alter large-scale weather patterns. While the system is deterministic—its future behavior is fully determined by its initial conditions—its chaotic nature makes long-term prediction practically impossible.

The behavior of the system depends on the choice of parameters. For some ranges of parameters, the system is predictable: trajectories settle into fixed points or simple periodic orbits, making the long-term behavior easy to describe. For example, when *ρ* < 1, all solutions converge to the origin, and for certain moderate values of ρ, σ, and β, solutions converge to symmetric steady states.

In contrast, for other parameter ranges, the system becomes chaotic. With the well-known parameters *σ* = 10, *ρ* = 28, and *β* = 8/3, the solutions never settle down but instead trace out the butterfly-shaped Lorenz attractor. In this regime, small differences in initial conditions grow exponentially.

## Overview

[edit]In 1963, Edward Lorenz developed the system as a simplified mathematical model for atmospheric convection.[1] He was attempting to model the way air moves when heated from below and cooled from above. The model describes how three key properties of this system change over time:

- x is proportional to the intensity of the convection (the rate of fluid flow).
- y is proportional to the temperature difference between the rising and falling air currents.
- z is proportional to the distortion of the vertical temperature profile from a linear one.

The model was developed with the assistance of Ellen Fetter, who performed the numerical simulations and created the figures,[1] and Margaret Hamilton, who aided in the initial computations.[2] The behavior of these three variables is governed by the following equations whose values change over time, which is defined as t:

- $${\displaystyle {\begin{aligned}{\frac {\mathrm {d} x}{\mathrm {d} t}}&=\sigma (y-x),\\[6pt]{\frac {\mathrm {d} y}{\mathrm {d} t}}&=x(\rho -z)-y,\\[6pt]{\frac {\mathrm {d} z}{\mathrm {d} t}}&=xy-\beta z.\end{aligned}}}$$

The constants σ, ρ, and β are parameters representing physical properties of the system: σ is the Prandtl number, ρ is the Rayleigh number, and β relates to the physical dimensions of the fluid layer itself.[3]

From a technical standpoint, the Lorenz system is nonlinear, aperiodic, three-dimensional, and deterministic. While originally for weather, the equations have since been found to model behavior in a wide variety of systems, including lasers,[4] dynamos,[5] electric circuits,[6] and even some chemical reactions.[7] The Lorenz equations have been the subject of hundreds of research articles and at least one book-length study.[3]

## Analysis

[edit]One normally assumes that the parameters σ, ρ, and β are positive. Lorenz used the values *σ* = 10, *ρ* = 28, and *β* = 8/3. The system exhibits chaotic behavior for these (and nearby) values.[8]

If *ρ* < 1 then there is only one equilibrium point, which is at the origin. This point corresponds to no convection. All orbits converge to the origin, which is a global attractor, when *ρ* < 1.[9]

A pitchfork bifurcation occurs at *ρ* = 1, and for *ρ* > 1 two additional equilibrium points appear at

- $${\displaystyle \rho <\sigma {\frac {\sigma +\beta +3}{\sigma -\beta -1}},}$$

which can hold only for positive ρ if *σ* > *β* + 1. At the critical value, both equilibrium points lose stability through a subcritical Hopf bifurcation.[10]

When *ρ* = 28, *σ* = 10, and *β* = 8/3, the Lorenz system has chaotic solutions (but not all solutions are chaotic). Almost all initial points will tend to an invariant set – the Lorenz attractor – a strange attractor, a fractal, and a self-excited attractor with respect to all three equilibria. Its Hausdorff dimension is estimated from above by the Lyapunov dimension (Kaplan-Yorke dimension) as 2.06±0.01,[11] and the correlation dimension is estimated to be 2.05±0.01.[12] The exact Lyapunov dimension formula of the global attractor can be found analytically under classical restrictions on the parameters:[13][11][14]

- $${\displaystyle 3-{\frac {2(\sigma +\beta +1)}{\sigma +1+{\sqrt {\left(\sigma -1\right)^{2}+4\sigma \rho }}}}}$$

The Lorenz attractor is difficult to analyze, but the action of the differential equation on the attractor is described by a fairly simple geometric model.[15] Proving that this is indeed the case is the fourteenth problem on the list of Smale's problems. This problem was the first one to be resolved, by Warwick Tucker in 2002.[16]

For other values of ρ, the system displays knotted periodic orbits. For example, with *ρ* = 99.96 it becomes a *T*(3,2) torus knot.

| Example solutions of the Lorenz system for different values of ρ | |
|---|---|
ρ = 14, σ = 10, β = 8/3 (Enlarge)
|
ρ = 13, σ = 10, β = 8/3 (Enlarge)
|
ρ = 15, σ = 10, β = 8/3 (Enlarge)
|
ρ = 28, σ = 10, β = 8/3 (Enlarge)
|
For small values of ρ, the system is stable and evolves to one of two fixed point attractors. When ρ > 24.74, the fixed points become repulsors and the trajectory is repelled by them in a very complex way.
|

| Sensitive dependence on the initial condition | ||
|---|---|---|
Time t = 1 (Enlarge)
|
Time t = 2 (Enlarge)
|
Time t = 3 (Enlarge)
|
These figures — made using ρ = 28, σ = 10, and β = 8/3 — show three time segments of the 3-dimensional evolution of two trajectories (one in blue, the other in yellow) in the Lorenz attractor starting at two initial points that differ only by 10−5 in the x-coordinate. Initially, the two trajectories seem coincident (only the yellow one can be seen, as it is drawn over the blue one) but, after some time, the divergence is obvious.
|

| Divergence of nearby trajectories. |
|---|
| Evolution of three initially nearby trajectories of the Lorenz system. In this animation the equation is numerically integrated using a Runge–Kutta routine — made using starting from three initial conditions (0.9, 0, 0) (green), (1.0, 0, 0) (blue) and (1.1, 0, 0) (red). Produced with WxMaxima. |
The parameters are: ρ = 28, σ = 10, and β = 8/3. Significant divergence is seen at around t = 24.0, beyond which the trajectories become uncorrelated. The full-sized graphic can be accessed here.
|

## Connection to the tent map

[edit]In Figure 4 of his paper,[1] Lorenz plotted the relative maximum value in the z direction achieved by the system against the previous relative maximum in the z direction. This procedure later became known as a Lorenz map (not to be confused with a Poincaré plot, which plots the intersections of a trajectory with a prescribed surface). The resulting plot has a shape very similar to the tent map. Lorenz also found that when the maximum z value is above a certain cut-off, the system will switch to the next lobe. Combining this with the chaos known to be exhibited by the tent map, he showed that the system switches between the two lobes chaotically.

## Simulations

[edit]```
using GLMakie
Base.@kwdef mutable struct Lorenz
dt::Float64 = 0.01
σ::Float64 = 10
ρ::Float64 = 28
β::Float64 = 8/3
x::Float64 = 1
y::Float64 = 1
z::Float64 = 1
end
function step!(l::Lorenz)
dx = l.σ * (l.y - l.x)
dy = l.x * (l.ρ - l.z) - l.y
dz = l.x * l.y - l.β * l.z
l.x += l.dt * dx
l.y += l.dt * dy
l.z += l.dt * dz
Point3f(l.x, l.y, l.z)
end
attractor = Lorenz()
points = Point3f[]
colors = Int[]
set_theme!(theme_black())
fig, ax, l = lines(points, color = colors,
colormap = :inferno, transparency = true,
axis = (; type = Axis3, protrusions = (0, 0, 0, 0),
viewmode = :fit, limits = (-30, 30, -30, 30, 0, 50)))
record(fig, "lorenz.gif", 1:120) do frame
for i in 1:50
push!(points, step!(attractor))
push!(colors, frame)
end
ax.azimuth[] = 1.7pi + 0.3 * sin(2pi * frame / 120)
Makie.update!(l, arg1 = points, color = colors) # Makie 0.24+
l.colorrange = (0, frame)
end
```

```
deq := [diff(x(t), t) = 10*(y(t) - x(t)), diff(y(t), t) = 28*x(t) - y(t) - x(t)*z(t), diff(z(t), t) = x(t)*y(t) - 8/3*z(t)]:
with(DEtools):
DEplot3d(deq, {x(t), y(t), z(t)}, t = 0 .. 100, [[x(0) = 10, y(0) = 10, z(0) = 10]], stepsize = 0.01, x = -20 .. 20, y = -25 .. 25, z = 0 .. 50, linecolour = sin(t*Pi/3), thickness = 1, orientation = [-40, 80], title = `Lorenz Chaotic Attractor`);
```

```
[sigma, rho, beta]: [10, 28, 8/3]$
eq: [sigma*(y-x), x*(rho-z)-y, x*y-beta*z]$
sol: rk(eq, [x, y, z], [1, 0, 0], [t, 0, 50, 1/100])$
len: length(sol)$
x: makelist(sol[k][2], k, len)$
y: makelist(sol[k][3], k, len)$
z: makelist(sol[k][4], k, len)$
draw3d(points_joined=true, point_type=-1, points(x, y, z), proportional_axes=xyz)$
```

```
% Solve over time interval [0,100] with initial conditions [1,1,1]
% ''f'' is set of differential equations
% ''a'' is array containing x, y, and z variables
% ''t'' is time variable
sigma = 10;
beta = 8/3;
rho = 28;
f = @(t,a) [-sigma*a(1) + sigma*a(2); rho*a(1) - a(2) - a(1)