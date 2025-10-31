export async function getServerSideProps() {
  return {
    redirect: {
      destination: '/upload',
      permanent: false,
    },
  };
}

export default function Home() {
  return null;
}
