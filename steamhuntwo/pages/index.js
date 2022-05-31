import Head from "next/head";
import styles from "../styles/Home.module.css";
import TextField from "@material-ui/core/TextField";
import AppBar from "@material-ui/core/AppBar";
import Button from "@material-ui/core/Button";

export default function Home() {
  return (
    <div className={styles.container}>
      <Head>
        <title>Steamhunt</title>
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <AppBar>
        <Button color="inherit">Login</Button>
      </AppBar>

      <main className={styles.main}>
        <h1 className={styles.title}>Steamhunt</h1>

        <form className={styles.form} autoComplete="off">
          <TextField
            id="standard-basic"
            label="Market Avatar URL"
            fullWidth
            margin="normal"
            InputLabelProps={{shrink: true}}
            helperText="https://steamcommunity-a.akamaihd.net/market/image/.../avatar.jpg"
          />
        </form>
      </main>

      <footer className={styles.footer}>Contact me</footer>
    </div>
  );
}
