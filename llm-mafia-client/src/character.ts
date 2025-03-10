import * as THREE from "../node_modules/@types/three";
import { Role, Character } from "./types";

// Character colors based on roles (only visible to the player for debugging)
const roleColors = {
  [Role.VILLAGER]: 0x3498db, // Blue
  [Role.MAFIA]: 0xe74c3c, // Red
  [Role.DETECTIVE]: 0x9b59b6, // Purple
  [Role.DOCTOR]: 0x2ecc71, // Green
};

export function createCharacter(
  role: Role,
  index: number,
  scene: THREE.Scene,
  isPlayer: boolean = false
): Character {
  // Create a group to hold all character parts
  const group = new THREE.Group();

  // Calculate position in a circle
  const radius = 8;
  const angle = (index / 7) * Math.PI * 2; // 7 characters total (player + 6 NPCs)
  const x = Math.cos(angle) * radius;
  const z = Math.sin(angle) * radius;

  // Set position
  const position = new THREE.Vector3(x, 0, z);
  group.position.copy(position);

  // Make character face the center
  group.lookAt(new THREE.Vector3(0, 0, 0));

  // Create character body
  const bodyGeometry = new THREE.CapsuleGeometry(0.5, 1, 4, 8);
  const bodyMaterial = new THREE.MeshStandardMaterial({
    color: 0xf5deb3, // Wheat color for body
    roughness: 0.7,
    metalness: 0.3,
  });
  const body = new THREE.Mesh(bodyGeometry, bodyMaterial);
  body.position.y = 1.25;
  body.castShadow = true;
  group.add(body);

  // Create character head
  const headGeometry = new THREE.SphereGeometry(0.4, 16, 16);
  const headMaterial = new THREE.MeshStandardMaterial({
    color: 0xf5deb3, // Wheat color for head
    roughness: 0.7,
    metalness: 0.3,
  });
  const head = new THREE.Mesh(headGeometry, headMaterial);
  head.position.y = 2.2;
  head.castShadow = true;
  group.add(head);

  // Create character clothes (indicates role, only visible to player for debugging)
  const clothesGeometry = new THREE.CylinderGeometry(0.6, 0.6, 1, 8);
  const clothesMaterial = new THREE.MeshStandardMaterial({
    color: roleColors[role],
    roughness: 0.8,
    metalness: 0.2,
  });
  const clothes = new THREE.Mesh(clothesGeometry, clothesMaterial);
  clothes.position.y = 1.25;
  clothes.scale.set(0.9, 0.9, 0.9);
  clothes.castShadow = true;
  group.add(clothes);

  // Add player number above character
  const playerNumber = isPlayer ? "YOU" : index.toString();

  // Create canvas for the text
  const canvas = document.createElement("canvas");
  canvas.width = 128;
  canvas.height = 64;
  const context = canvas.getContext("2d");
  if (context) {
    context.fillStyle = "rgba(0, 0, 0, 0)";
    context.fillRect(0, 0, canvas.width, canvas.height);

    // Text styling
    context.font = "bold 48px Arial";
    context.textAlign = "center";
    context.textBaseline = "middle";

    // Draw text
    if (isPlayer) {
      // Player's character gets a special color
      context.fillStyle = "#FF9900"; // Orange
      context.fillText(playerNumber, canvas.width / 2, canvas.height / 2);
    } else {
      context.fillStyle = "white";
      context.fillText(playerNumber, canvas.width / 2, canvas.height / 2);
    }
  }

  // Create texture from canvas
  const texture = new THREE.CanvasTexture(canvas);

  // Create sprite material with the texture
  const spriteMaterial = new THREE.SpriteMaterial({
    map: texture,
    transparent: true,
  });

  // Create sprite and position it above the character
  const sprite = new THREE.Sprite(spriteMaterial);
  sprite.position.y = 3.0;
  sprite.scale.set(1.5, 0.75, 1);
  group.add(sprite);

  // If this is the player's character, add a marker
  if (isPlayer) {
    // Add a glowing ring around the player's character
    const ringGeometry = new THREE.TorusGeometry(0.8, 0.05, 16, 32);
    const ringMaterial = new THREE.MeshStandardMaterial({
      color: 0xff9900, // Orange
      emissive: 0xff9900,
      emissiveIntensity: 2,
    });
    const ring = new THREE.Mesh(ringGeometry, ringMaterial);
    ring.position.y = 0.05; // Just above the ground
    ring.rotation.x = Math.PI / 2; // Lay flat
    group.add(ring);
  }

  // Add character to scene
  scene.add(group);

  // Create a simple animation for the character
  let animationTime = Math.random() * Math.PI * 2; // Random start time

  // Return the character object
  return {
    model: group,
    position,
    update: () => {
      // Simple idle animation
      animationTime += 0.01;

      // Subtle bobbing motion
      group.position.y = Math.sin(animationTime) * 0.1;

      // Subtle rotation
      group.rotation.y =
        Math.sin(animationTime * 0.5) * 0.1 + group.rotation.y * 0.99;
    },
  };
}
