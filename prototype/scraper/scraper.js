require("dotenv").config();
const mongoose = require("mongoose");
const axios = require("axios");

const SteamUserSchema = new mongoose.Schema({
  steamid: {type: String, unique: true},
  friends: Array,
  friendsLastChecked: Date,
  friendsVisible: Boolean,
});

const SteamUser = mongoose.model("SteamUser", SteamUserSchema);

const InsertEmptySteamUser = (sid) => {
  const user = new SteamUser({
    steamid: sid,
    friends: [],
    friendsLastChecked: 0,
    getPlayerSummariesLastChecked: 0,
    avatarLastDownloaded: 0,
    friendsVisible: true,
  });

  user.save((err, user) => {});
};

const NUsersToFriendScan = async (n) => {
  const steamids = (
    await SteamUser.aggregate([
      {$sort: {friendsLastChecked: 1}},
      {$limit: n},
      {$match: {friendsVisible: true}},
    ])
  ).map((response) => response.steamid);

  return steamids;
};

const DownloadFriends = async (sid) => {
  try {
    const resp = await axios.get(
      `http://api.steampowered.com/ISteamUser/GetFriendList/v0001/?key=${process.env.STEAM_API}&steamid=${sid}&relationship=friend`
    );

    return [
      true,
      resp.data["friendslist"]["friends"].map((friend) => friend.steamid),
    ];
  } catch (error) {
    if (error.response) {
      if (error.response.status == 401) {
        await SetFriendVis(sid);
        return [false, []];
      }
    }
    throw error;
  }
};

const SetFriendVis = async (sid) => {
  await SteamUser.updateOne({steamid: sid}, {friendsVisible: false});
};

const UpdateFriends = async (sid, friends) => {
  await SteamUser.updateOne(
    {steamid: sid},
    {friends: friends, friendsLastChecked: Date.now()}
  );
};

const options = {
  useNewUrlParser: true,
  useUnifiedTopology: true,
  useCreateIndex: true,
};

const connectWithRetry = () => {
  console.log("MongoDB connection with retry");
  mongoose
    .connect(process.env.MONGO_URI, options)
    .then(async () => {
      console.log("MongoDB is connected");

      while (true) {
        try {
          console.log("!! GETTING SIDS TO SCAN !!");

          // get some sids to scan
          const batchSize = parseInt(process.env.BATCH_SIZE);
          const sids = await NUsersToFriendScan(batchSize);

          console.log("!! DOWNLOADING FRIENDS !!");

          // Download friends lists
          const allFriends = await Promise.all(
            sids.map((sid) => DownloadFriends(sid))
          );

          console.log("!! UPDATING FRIENDS LISTS !!");

          allFriends.forEach((friends, index) => {
            [isVisible, friendsList] = friends;
            if (isVisible) {
              UpdateFriends(sids[index], friendsList);
            } else {
              SetFriendVis(sids[index]);
            }
          });

          console.log(`!! INSERTING ${allFriends.length} NEW USERS !!`);

          // Insert new friends records' into DB
          const responses = await Promise.all(
            allFriends
              .filter((val) => val[0])
              .map((p) => p[1])
              .reduce((acc, val) => acc.concat(val), [])
              .map((friend) => InsertEmptySteamUser(friend))
          );

          console.log("!! DONE ONE ROUND !!");
        } catch (err) {
          console.error(err);
        }
      }
    })
    .catch((err) => {
      console.log(err);
      console.log("MongoDB connection unsuccessful, retry after 5 seconds.");
      setTimeout(connectWithRetry, 5000);
    });
};

const main = async () => {
  try {
    console.log("!! CONNECTING TO DATABASE !!");
    connectWithRetry();
  } catch (err) {
    console.log("error:", err);
  }
};

main();
