import * as THREE from "../node_modules/@types/three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";

export function setupScene() {
  // Create scene
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x222222);

  // Add ambient light
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
  scene.add(ambientLight);

  // Add directional light
  const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
  directionalLight.position.set(5, 10, 7.5);
  directionalLight.castShadow = true;
  directionalLight.shadow.mapSize.width = 2048;
  directionalLight.shadow.mapSize.height = 2048;
  scene.add(directionalLight);

  // Create camera
  const camera = new THREE.PerspectiveCamera(
    75,
    window.innerWidth / window.innerHeight,
    0.1,
    1000
  );
  camera.position.set(0, 10, 15);

  // Create renderer
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  document.getElementById("game-container")?.appendChild(renderer.domElement);

  // Create controls
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.05;
  controls.screenSpacePanning = false;
  controls.minDistance = 5;
  controls.maxDistance = 30;
  controls.maxPolarAngle = Math.PI / 2;

  // Create ground
  const groundGeometry = new THREE.PlaneGeometry(50, 50);
  const groundMaterial = new THREE.MeshStandardMaterial({
    color: 0x1a5e1a,
    roughness: 0.8,
    metalness: 0.2,
  });
  const ground = new THREE.Mesh(groundGeometry, groundMaterial);
  ground.rotation.x = -Math.PI / 2;
  ground.receiveShadow = true;
  scene.add(ground);

  // Add a simple village environment
  createVillageEnvironment(scene);

  // Handle window resize
  window.addEventListener("resize", () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });

  return { scene, camera, renderer, controls };
}

function createVillageEnvironment(scene: THREE.Scene) {
  // Create a circle of houses around the center
  const houseCount = 8;
  const radius = 15;

  for (let i = 0; i < houseCount; i++) {
    const angle = (i / houseCount) * Math.PI * 2;
    const x = Math.cos(angle) * radius;
    const z = Math.sin(angle) * radius;

    createHouse(scene, x, z, angle);
  }

  // Create a central meeting area
  const centerGeometry = new THREE.CircleGeometry(5, 32);
  const centerMaterial = new THREE.MeshStandardMaterial({
    color: 0x888888,
    roughness: 0.7,
    metalness: 0.1,
  });
  const centerArea = new THREE.Mesh(centerGeometry, centerMaterial);
  centerArea.rotation.x = -Math.PI / 2;
  centerArea.position.y = 0.01; // Slightly above ground to prevent z-fighting
  centerArea.receiveShadow = true;
  scene.add(centerArea);

  // Add a campfire in the center
  const fireGeometry = new THREE.ConeGeometry(0.5, 1, 8);
  const fireMaterial = new THREE.MeshStandardMaterial({
    color: 0xff3300,
    emissive: 0xff5500,
    emissiveIntensity: 2,
  });
  const fire = new THREE.Mesh(fireGeometry, fireMaterial);
  fire.position.set(0, 0.5, 0);
  scene.add(fire);

  // Add a point light for the fire
  const fireLight = new THREE.PointLight(0xff5500, 1, 10);
  fireLight.position.set(0, 1, 0);
  scene.add(fireLight);
}

function createHouse(
  scene: THREE.Scene,
  x: number,
  z: number,
  rotation: number
) {
  // House group
  const house = new THREE.Group();
  house.position.set(x, 0, z);
  house.rotation.y = rotation + Math.PI; // Face toward center

  // House body
  const bodyGeometry = new THREE.BoxGeometry(3, 2, 2);
  const bodyMaterial = new THREE.MeshStandardMaterial({
    color: 0xd2b48c,
    roughness: 0.8,
    metalness: 0.2,
  });
  const body = new THREE.Mesh(bodyGeometry, bodyMaterial);
  body.position.y = 1;
  body.castShadow = true;
  body.receiveShadow = true;
  house.add(body);

  // Roof
  const roofGeometry = new THREE.ConeGeometry(2.5, 1.5, 4);
  const roofMaterial = new THREE.MeshStandardMaterial({
    color: 0x8b4513,
    roughness: 0.8,
    metalness: 0.2,
  });
  const roof = new THREE.Mesh(roofGeometry, roofMaterial);
  roof.position.y = 2.75;
  roof.rotation.y = Math.PI / 4;
  roof.castShadow = true;
  house.add(roof);

  // Door
  const doorGeometry = new THREE.PlaneGeometry(0.6, 1.2);
  const doorMaterial = new THREE.MeshStandardMaterial({
    color: 0x8b4513,
    roughness: 0.8,
    metalness: 0.2,
  });
  const door = new THREE.Mesh(doorGeometry, doorMaterial);
  door.position.set(0, 0.6, 1.01);
  house.add(door);

  // Window
  const windowGeometry = new THREE.PlaneGeometry(0.5, 0.5);
  const windowMaterial = new THREE.MeshStandardMaterial({
    color: 0xadd8e6,
    roughness: 0.3,
    metalness: 0.8,
  });

  // Left window
  const leftWindow = new THREE.Mesh(windowGeometry, windowMaterial);
  leftWindow.position.set(-0.7, 1.2, 1.01);
  house.add(leftWindow);

  // Right window
  const rightWindow = new THREE.Mesh(windowGeometry, windowMaterial);
  rightWindow.position.set(0.7, 1.2, 1.01);
  house.add(rightWindow);

  scene.add(house);
}
