def generateVideo(self, jsonData, imgPath, lineY1, lineY2):
        img_array = []

        for idx, filename in enumerate(glob.glob(imgPath + "*.png")):
            img = cv2.imread(filename)
            lineThickness = 3
            cv2.line(img, (0, lineY), (1920, lineY),
                     (255, 0, 0), lineThickness)
            self.drawBoundingBox(img, self.filterByClass(
                self.getEntitiesBetwixtX(jsonData[idx], lineY), int(self.filterRbValue.get())))
            height, width, layers = img.shape
            size = (width, height)
            img_array.append(img)

        out = cv2.VideoWriter(
            'project.avi', cv2.VideoWriter_fourcc(*'DIVX'), 15, size)

        for i in range(len(img_array)):
            out.write(img_array[i])
        out.release()