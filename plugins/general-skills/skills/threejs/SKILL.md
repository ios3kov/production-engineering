---
name: threejs
description: "Build and review browser-based interactive 3D with Three.js: scene structure, cameras, lighting, GLTF assets, materials, animation, shaders, interaction and rendering performance."
---

# Three.js

Use only when browser 3D, WebGL, GLTF/GLB, scene rendering or Three.js is actually relevant. Static mockups and ordinary UI usually do not need a 3D engine.

## Approach

1. Determine the goal and runtime: decorative hero, interactive product view, data experience or 3D tool. Verify the project's Three.js version and WebGL/WebGPU needs.
2. Define the scene graph: objects, geometry, materials, cameras, lighting, environment, fog, coordinate system and transforms. Use the simplest representation that meets the requirement.
3. Plan controls and interactions: pointer/touch/keyboard input, raycasting where needed, smooth camera movement, and accessible alternatives.
4. Use asynchronous loaders for GLTF assets/textures, with visible loading/error states; credit and license imported assets appropriately.
5. Handle responsive resizing, appropriate device pixel ratio, stable delta-time animation and disposal of geometries/materials/textures/render targets/events.
6. Profile: draw calls, material/shader complexity, triangles, texture sizes, shadows, postprocessing, particle count, frame timing. Use instancing and LOD when measurements justify them.
7. Provide a fallback for unsupported hardware and a reduced-motion pathway. Avoid autoplay scenes that block page interactions.
8. Test actual rendering and controls in a browser; do not claim visual correctness from unexecuted code.

## Output

For planning, deliver scene inventory, interaction spec, asset list and performance budget. For implementation, provide working code and verification steps compatible with the detected project version.

## Source

Adapted from [CloudAI-X/threejs-skills](https://github.com/CloudAI-X/threejs-skills). Version-sensitive details should be checked against [Three.js documentation](https://threejs.org/docs/).
