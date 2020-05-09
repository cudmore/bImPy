

run("Blobs (25K)"); // just a sample image that comes with Fiji
//run("Threshold...");
setAutoThreshold("Default"); // use auto-threshold method...
run("Create Mask"); // make binary
originalMask = getImageID();
run("Analyze Particles...", "size=200-Infinity add"); // select objects within based on certain size
roiManager("Fill"); // fill in those ROIs...

// do another round of thresholding and mask creation based on those 'tiny' objects you want to exclude
setAutoThreshold("Default dark");
run("Create Mask");
subsetMask = getImageID();
imageCalculator("Subtract create", originalMask, subsetMask); // simply subtract the 'tiny' objects from the original mask

// last round of thresholding... to get the final binary image
//run("Threshold...");
setAutoThreshold("Default dark");
setAutoThreshold("Huang dark");
run("Create Mask");