FROM node

# create app directory
WORKDIR /usr/src/scraper

# copy dependencies
COPY package-lock.json ./

# install dependencies
RUN npm install

# bundle app source
COPY . .

CMD [ "node", "scraper.js" ]
